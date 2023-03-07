import asyncio
import logging
from enum import Enum
from typing import Coroutine, Any, Dict

from aiomox.device.device import Device, _get_msg_type
from aiomox.mox_client import MoxClient

_LOGGER = logging.getLogger(__name__)
# Callback message codes
POS_STATE_MESSAGE: bytes = b'\x01\x00\x00\x03\x04'


class StateType(Enum):
    POSITION = 1


class Curtain(Device):
    _position: int = None

    def __init__(self, device_id: int, mox_client: MoxClient, on_state_change: Coroutine[Any, Any, None] = None):
        super().__init__(device_id, mox_client)

        # prepare protocol messages
        self._get_position_msg: bytes = b'\x02' + self._device_id + b'\x01\x00\x00\x01\x02'
        self._set_position_msg: bytes = b'\x03' + self._device_id + b'\x01\x00\x00\x02\x04'

        if on_state_change is not None:
            self.set_state_change_callback(StateType.POSITION, on_state_change)

        # invoke a callback to update the state of this device
        asyncio.create_task(self.request_state_update())

    async def _update_callback(self, message: bytes) -> None:
        await super()._update_callback(message)
        if _get_msg_type(message) == POS_STATE_MESSAGE:
            if len(message) != 12:
                raise Exception(f"Invalid message length: {len(message)}. Expected length: 12. Msg: {message.hex()}")
            new_position = message[10]
            if self._position != new_position:
                self._position = new_position
                await self.invoke_state_change_callback(StateType.POSITION)
        else:
            _LOGGER.debug(f"Ignoring unknown message type for message: {message.hex()}")

    def _is_valid_state_type(self, state_type) -> bool:
        return state_type in StateType or super()._is_valid_state_type(state_type)

    def get_position(self) -> int:
        """Return the current position of the curtain"""
        return self._position

    async def set_position(self, position: int = None) -> None:
        """Set the position of the curtain

        Keyword arguments:
        position -- The desired position for the curtain. Value should be between 0 (closed) and 100 (open)
        """
        if position is None or position < 0 or position > 100:
            raise ValueError(f"Illegal value for position: {position}, It must be between 0 and 100")
        await self._mox_client.send_message(self._set_position_msg +
                                            position.to_bytes(length=1, byteorder="little", signed=False) +
                                            b'\x00')

    async def request_state_update(self) -> None:
        await self._mox_client.send_message(self._get_position_msg)
