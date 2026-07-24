import pytest

from app.websocket.manager import ConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.messages = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message):
        self.messages.append(message)


@pytest.mark.asyncio
async def test_personal_websocket_messages_do_not_cross_tenants():
    manager = ConnectionManager()
    tenant_a_socket = FakeWebSocket()
    tenant_b_socket = FakeWebSocket()
    await manager.connect(tenant_a_socket, user_id="same-user", organization_id="tenant-a")
    await manager.connect(tenant_b_socket, user_id="same-user", organization_id="tenant-b")

    await manager.send_to_user({"event": "private"}, "tenant-a", "same-user")

    assert len(tenant_a_socket.messages) == 1
    assert tenant_b_socket.messages == []
