import asyncio
import logging
from enum import Enum
from typing import Coroutine, Any, Dict

from aiomox.device.device import _get_msg_type
from aiomox.device.switch import Switch
from aiomox.mox_client import MoxClient

_LOGGER = logging.getLogger(__name__)
# Callback message codes
LUM_STATE_MESSAGE: bytes = b'\x03\x00\x00\x03\x04'


class StateType(Enum):
    LUMINOUS = 1


def _validate_percentage(percentage):
    """Validate the value is a percentage"""
    if percentage is None or percentage < 0 or percentage > 100:
        raise ValueError(f"Illegal value for percentage: {percentage}, It must be between 0 and 100")


class Dimmer(Switch):
    _luminous: int = None

    def __init__(self, device_id: int, mox_client: MoxClient, on_state_change: Coroutine[Any, Any, None] = None):
        super().__init__(device_id, mox_client)

        # prepare protocol messages
        self._increase_msg_prefix: bytes = b'\x07' + self._device_id + b'\x01\x00\x00\x04\x06'
        self._increase_msg_suffix: bytes = b'\x00\x08\x00'
        self._decrease_msg_prefix: bytes = b'\x07' + self._device_id + b'\x02\x00\x00\x04\x06'
        self._decrease_msg_suffix: bytes = b'\x00\x08\x00'
        self._get_luminous_msg: bytes = b'\x02' + self._device_id + b'\x03\x00\x00\x01\x02'
        self._set_luminous_msg: bytes = b'\x03' + self._device_id + b'\x02\x00\x00\x02\x06'

        if on_state_change is not None:
            self.set_state_change_callback(StateType.LUMINOUS, on_state_change)

        # invoke a callback to update the state of this device
        asyncio.create_task(self.request_state_update())

    def get_luminous(self):
        """Get the current level of luminous"""
        return self._luminous

    async def increase(self, step: int = 10) -> None:
        """Increase the level of brightness (step is between 0 and 100)"""
        _validate_percentage(step)
        await self._mox_client.send_message(self._increase_msg_prefix +
                                            step.to_bytes(length=1, byteorder="little", signed=False) +
                                            self._increase_msg_suffix)

    async def decrease(self, step: int = 10) -> None:
        """Decrease the level of brightness (step is between 0 and 100)"""
        _validate_percentage(step)
        await self._mox_client.send_message(self._decrease_msg_prefix +
                                            step.to_bytes(length=1, byteorder="little", signed=False) +
                                            self._decrease_msg_suffix)

    def _is_valid_state_type(self, state_type) -> bool:
        return state_type in StateType or super()._is_valid_state_type(state_type)

    async def set_luminous(self, level: int, transition_time: int = 1000) -> None:
        """Set level of brightness

        Keyword arguments:
        level -- The level of brightness (between 0 and 100)
        transition_time -- The time to transition from the current level to the new level in milliseconds
        (between 0 and 32767)
        """
        _validate_percentage(level)
        await self._mox_client.send_message(self._set_luminous_msg +
                                            level.to_bytes(length=1, byteorder="little", signed=False) +
                                            b'\x00' +
                                            transition_time.to_bytes(length=2, byteorder="little", signed=False))

    async def _update_callback(self, message: bytes) -> None:
        await super()._update_callback(message)
        if _get_msg_type(message) == LUM_STATE_MESSAGE:
            lum = message[10]
            if self._luminous != lum:
                self._luminous = lum
                await self.invoke_state_change_callback(StateType.LUMINOUS)
                await self._update_on_off_state(bool(lum))
        else:
            _LOGGER.debug(f"Ignoring unknown message type for message: {message.hex()}")

    def _is_valid_state_type(self, state_type) -> bool:
        return state_type in StateType or super()._is_valid_state_type(state_type)

    async def request_state_update(self) -> None:
        await self._mox_client.send_message(self._get_luminous_msg)