from abc import ABC, abstractmethod
from enum import Enum
from typing import Coroutine, Any, Dict

from aiomox.mox_client import MoxClient


def _get_msg_type(message: bytes) -> bytes:
    """Return the bytes that contain the message type"""
    if len(message) < 10:
        raise ValueError(f"Unable to extract message type from message {message.hex()}")
    return message[5:10]


class Device(ABC):
    _device_id: bytes = None
    _device_id_int: int = None
    _mox_client: MoxClient = None
    _state_change_callbacks: Dict[Enum, Coroutine[Any, Any, None]] = None

    def __init__(self, device_id: int, mox_client: MoxClient):
        """Create new device

        Keyword arguments:
            device_id -- The unique ID of the device, based on 4 bits [oid_h, oid_m, oid_l, suboid] example: 0x0000CB12
            mox_client -- An open connection to the MOX Gateway
        """
        self._device_id = device_id.to_bytes(length=4, byteorder='big', signed=False)
        self._device_id_int = device_id
        self._mox_client = mox_client
        self._state_change_callbacks = {}
        self._mox_client.register_callback(self._device_id, self._update_callback)

    def set_state_change_callback(self, state_type: Enum, callback: Coroutine[Any, Any, None]) -> None:
        """Register a Coroutine to be executed on and change of the provided state_type

        Keyword Arguments:
            state_type -- The string representing the type of state change the callback should be invoked on
            callback -- a Coroutine with the signature (Device, str) -> None. The device object and the string
            representing the state changed will be passed when executing the Coroutine
        """
        if self._is_valid_state_type(state_type):
            self._state_change_callbacks[state_type] = callback
        else:
            raise ValueError(f'Unsupported state type: {state_type}')

    async def invoke_state_change_callback(self, state_type: Enum) -> None:
        callback = self._state_change_callbacks.get(state_type)
        if callback is not None:
            await callback(self, state_type)

    @abstractmethod
    def _is_valid_state_type(self, state_type) -> bool:
        """validate that the given state type is supported by this device"""
        return False

    @abstractmethod
    async def _update_callback(self, message: bytes) -> None:
        """A callback method to be invoked whenever the MOX Gateway issues a state update"""
        pass

    def get_device_id(self) -> int:
        """Get this devices ID"""
        return self._device_id_int

    @abstractmethod
    async def request_state_update(self) -> None:
        """Request the MOX Gateway to send a message containing the state of this device"""
        pass
