import asyncio
import logging
from enum import Enum
from typing import Coroutine, Any, Dict

from aiomox.device.device import Device, _get_msg_type
from aiomox.mox_client import MoxClient

_LOGGER = logging.getLogger(__name__)
# Callback message codes
STATE_MESSAGE: bytes = b'\x01\x00\x00\x03\x03'


class StateType(Enum):
    ON_OFF = "ON_OFF"


class Switch(Device):
    _is_on: bool = False

    def __init__(self, device_id: int, mox_client: MoxClient, on_state_change: Coroutine[Any, Any, None] = None):
        super().__init__(device_id, mox_client)

        # prepare protocol messages
        self._get_state_msg: bytes = b'\x02' + self._device_id + b'\x01\x00\x00\x01\x02'
        self._turn_on_msg: bytes = b'\x02' + self._device_id + b'\x01\x00\x00\x02\x03\x01'
        self._turn_off_msg: bytes = b'\x02' + self._device_id + b'\x01\x00\x00\x02\x03\x00'

        if on_state_change is not None:
            self.set_state_change_callback(StateType.ON_OFF, on_state_change)

        # invoke a callback to update the state of this device
        asyncio.create_task(self.request_state_update())

    async def _update_callback(self, message: bytes) -> None:
        await super()._update_callback(message)
        if _get_msg_type(message) == STATE_MESSAGE:
            if len(message) != 11:
                raise Exception(f"Invalid message length: {len(message)}. Expected length: 11. Msg: {message.hex()}")
            await self._update_on_off_state(bool(message[10]))
        else:
            _LOGGER.debug(f"Ignoring unknown message type for message: {message.hex()}")

    async def _update_on_off_state(self, new_state: bool):
        if self._is_on != new_state:
            self._is_on = new_state
            await self.invoke_state_change_callback(StateType.ON_OFF)

    def _is_valid_state_type(self, state_type) -> bool:
        return state_type in StateType or super()._is_valid_state_type(state_type)

    def is_on(self) -> bool:
        """Return True if the switch is on"""
        return self._is_on

    async def turn_off(self) -> None:
        """Turn off the switch"""
        await self._mox_client.send_message(self._turn_off_msg)

    async def turn_on(self) -> None:
        """Turn on the switch"""
        await self._mox_client.send_message(self._turn_on_msg)

    async def request_state_update(self) -> None:
        await self._mox_client.send_message(self._get_state_msg)
