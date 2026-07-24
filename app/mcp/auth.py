import json
import urllib.request
from typing import Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.api.dependencies import TenantContext, get_container_dependency
from app.settings import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)

def _get_oidc_public_keys(issuer: str):
    """Fetch OIDC public keys from the issuer."""
    # In production, this should be cached heavily
    try:
        config_url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
        with urllib.request.urlopen(config_url) as response:
            config = json.loads(response.read())
        jwks_uri = config.get("jwks_uri")
        if not jwks_uri:
            return None
        with urllib.request.urlopen(jwks_uri) as response:
            jwks = json.loads(response.read())
        return jwks
    except Exception as e:
        import logging
        logging.error(f"Failed to fetch OIDC keys from {issuer}: {e}")
        return None

async def authenticate_mcp_request(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> TenantContext:
    """
    Authenticate MCP request using either API key or OIDC token.
    Returns the resolved TenantContext.
    """
    settings = get_settings()
    container = await get_container_dependency()
    tenant_service = container.get("tenant_service")

    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant service not initialized"
        )

    # 1. Try API Key authentication
    key_to_check = api_key
    if not key_to_check and bearer and not bearer.credentials.startswith("ey"):
        # Sometimes API keys are passed in Bearer token if they aren't JWTs
        key_to_check = bearer.credentials

    if key_to_check:
        ctx_dict = await tenant_service.validate_api_key(key_to_check)
        if ctx_dict:
            org_id = ctx_dict["organization_id"]
            return TenantContext(
                organization_id=org_id,
                organization_slug=ctx_dict["organization_slug"],
                key_type=ctx_dict["key_type"],
                scopes=ctx_dict["scopes"],
                plan=ctx_dict["plan"],
                config=ctx_dict["config"],
                collection_name=f"tenant_{org_id}_products"
            )

    # 2. Try OIDC authentication
    if bearer and bearer.credentials:
        token = bearer.credentials
        issuer = settings.MCP_OIDC_ISSUER
        audience = settings.MCP_OIDC_AUDIENCE

        if issuer and audience:
            try:
                # In a real system, we'd fetch and cache the JWKS, and pass it as the key.
                # For this implementation, we simulate decoding or rely on a known symmetric key if issuer is local,
                # but OIDC usually requires RS256 with JWKS.
                jwks = _get_oidc_public_keys(issuer)
                if not jwks:
                    raise HTTPException(status_code=401, detail="Failed to fetch OIDC public keys")

                unverified_header = jwt.get_unverified_header(token)
                rsa_key = {}
                for key in jwks.get("keys", []):
                    if key["kid"] == unverified_header.get("kid"):
                        rsa_key = {
                            "kty": key["kty"],
                            "kid": key["kid"],
                            "use": key["use"],
                            "n": key["n"],
                            "e": key["e"]
                        }
                        break

                if not rsa_key:
                    raise HTTPException(status_code=401, detail="OIDC Public key not found")

                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=audience,
                    issuer=issuer,
                )

                org_id = payload.get("organization_id") or payload.get("org_id") or payload.get("tenant_id")
                if not org_id:
                    raise HTTPException(status_code=401, detail="OIDC token missing organization claim")

                # We need to construct a TenantContext for this OIDC service account
                # For simplicity, we assume OIDC tokens map to the tenant with a default 'service_account' plan
                return TenantContext(
                    organization_id=org_id,
                    organization_slug=org_id, # Might need a lookup in production
                    key_type="oidc_service_account",
                    scopes=payload.get("scope", "").split(),
                    plan="service_account",
                    config={},
                    collection_name=f"tenant_{org_id}_products"
                )

            except JWTError as e:
                raise HTTPException(status_code=401, detail=f"Invalid OIDC token: {str(e)}")

        # Fallback to local JWT if not OIDC
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            org_id = payload.get("organization_id") or payload.get("org_id")
            if org_id:
                return TenantContext(
                    organization_id=org_id,
                    organization_slug=org_id,
                    key_type="jwt_user",
                    scopes=payload.get("roles", ["user"]),
                    plan="jwt",
                    config={},
                    collection_name=f"tenant_{org_id}_products"
                )
        except JWTError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid MCP authentication credentials required (API Key or OIDC token)"
    )
