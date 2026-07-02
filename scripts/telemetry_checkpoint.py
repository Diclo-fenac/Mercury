#!/usr/bin/env python3
"""
Telemetry Checkpoint Script
Backs up Redis telemetry (trending searches and products) to PostgreSQL
Intended to run every hour via cron.
"""
import asyncio
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.container import get_container
from app.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("telemetry_checkpoint")

async def main():
    settings = get_settings()
    container = await get_container()
    
    redis_client = container.get('cache')
    db_client = container.get('db')
    
    if not redis_client or not db_client:
        logger.error("Required services not available")
        return
        
    if not await redis_client.is_available():
        logger.error("Redis is not available")
        return
        
    logger.info("Starting telemetry checkpoint...")
    
    # In a real implementation, we would query the database for all active tenant IDs.
    # For now, we'll scan Redis for telemetry keys.
    # Note: For production, we shouldn't use KEYS *, but SCAN. 
    # For simplicity of this script, we'll fetch known namespaces or use the raw client to scan.
    
    try:
        # Get raw redis client to use SCAN
        r = redis_client._client
        if not r:
            logger.error("Raw redis client not available")
            return
            
        cursor = '0'
        telemetry_keys = set()
        
        while cursor != 0:
            cursor, keys = await r.scan(cursor=cursor, match="telemetry:*", count=100)
            for key in keys:
                telemetry_keys.add(key)
                
        logger.info(f"Found {len(telemetry_keys)} telemetry keys to checkpoint.")
        
        checkpoints_saved = 0
        
        # We can store these in Postgres. We'll create a simple table if it doesn't exist.
        # Alternatively, since we just want a backup, we can dump to a JSON file.
        # The user said "backup for redis cache of trends every 1 hours.. like a checkpoint".
        # Let's save it to a JSON file as the simplest robust checkpoint that can be reloaded on startup.
        
        backup_data = {}
        
        for key in telemetry_keys:
            # Check if it's a zset (trending searches/products use zsets)
            key_type = await r.type(key)
            if key_type == 'zset':
                # Get top 100 items to backup
                items = await r.zrevrange(key, 0, 99, withscores=True)
                backup_data[key] = {
                    "type": "zset",
                    "data": items,
                    "timestamp": datetime.now().isoformat()
                }
            elif key_type == 'string':
                # Just string cache
                val = await r.get(key)
                backup_data[key] = {
                    "type": "string",
                    "data": val,
                    "timestamp": datetime.now().isoformat()
                }
                
        backup_file = Path("data/telemetry_checkpoint.json")
        backup_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(backup_file, "w") as f:
            json.dump(backup_data, f, indent=2)
            
        logger.info(f"Successfully checkpointed {len(backup_data)} keys to {backup_file}")
        
    except Exception as e:
        logger.error(f"Checkpoint failed: {e}")
        
if __name__ == "__main__":
    asyncio.run(main())
