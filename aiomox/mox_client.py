import asyncio
import logging
from asyncio import Transport, Future
from typing import Dict, Coroutine, Any

from aiomox.lt_can_client_protocol import LTCANClientProtocol

_LOGGER = logging.getLogger(__name__)

DEFAULT_CLIENT_HOST = '0.0.0.0'
DEFAULT_CLIENT_PORT = 6666
DEFAULT_GW_HOST = '172.16.254.254'
DEFAULT_GW_PORT = 6670


class MoxClient:
    """Client component to facilitate communication with the MOX gateway """

    _transport: Transport = None
    _devices: Dict[bytes, Coroutine[Any, Any, None]] = {}

    def __init__(self,
                gateway_host: str = DEFAULT_GW_HOST,
                gateway_port: int = DEFAULT_GW_PORT,
                client_host: str = DEFAULT_CLIENT_HOST,
                client_port: int = DEFAULT_CLIENT_PORT):
        """Client for communication with the MOX Gateway"""
        self._gateway_host: str = gateway_host
        self._gateway_port: int = gateway_port
        self._client_host: str = client_host
        self._client_port: int = client_port

    async def connect(self, on_con_lost: Future) -> None:
        assert self._transport is None
        _LOGGER.info("Connecting to MOX Gateway")
        loop = asyncio.get_running_loop()
        self._transport, protocol = await loop.create_datagram_endpoint(
            lambda: LTCANClientProtocol(on_con_lost, self._on_message),
            remote_addr=(self._gateway_host, self._gateway_port),
            local_addr=(self._client_host, self._client_port))

    async def close(self) -> None:
        """Close the connection"""
        assert self._transport is not None
        _LOGGER.info("Closing connection")
        self._transport.close()

    async def _on_message(self, data: bytes) -> None:
        """Trigger a callback if the device is registered"""
        device_id = data[1:5]
        callback = self._devices.get(device_id)
        if callback is not None:
            _LOGGER.debug(f"Invoking callback for device: {device_id.hex()}")
            await callback(data)

    def register_callback(self, device_id: bytes, callback: Coroutine[Any, Any, None]) -> None:
        """Registers devices so that their callbacks would be executed on state changes"""
        _LOGGER.info(f"Registering callback for device: {device_id.hex()}")
        self._devices[device_id] = callback

    async def send_message(self, data: bytes) -> None:
        """Send a message to the MOX gateway"""
        assert self._transport is not None
        _LOGGER.debug(f'Sending message: {data.hex()}')
        self._transport.sendto(data)
