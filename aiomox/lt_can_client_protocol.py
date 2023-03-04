import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class LTCANClientProtocol(asyncio.DatagramProtocol):
    _background_tasks: set = set()

    def __init__(self, on_con_lost, on_receive):
        self.on_con_lost = on_con_lost
        self.on_receive = on_receive
        self.transport = None

    def connection_made(self, transport):
        _LOGGER.info(f"LT CAN connection established")
        self.transport = transport

    def datagram_received(self, data, addr):
        _LOGGER.debug(f"Received: {data.hex()} from {addr}")
        task = asyncio.create_task(self.on_receive(data))
        # Add task to the set. This creates a strong reference.
        self._background_tasks.add(task)
        # Remove task from set when done.
        task.add_done_callback(self._background_tasks.discard)

    def error_received(self, exc):
        _LOGGER.error(f'Error received: {exc}')

    def connection_lost(self, exc):
        _LOGGER.info("Connection closed")
        self.transport = None
        self.on_con_lost.set_result(True)
