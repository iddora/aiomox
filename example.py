import asyncio
import logging

from aiomox.device.curtain import Curtain, StateType as CST
from aiomox.device.dimmer import Dimmer, StateType as DST
from aiomox.device.switch import Switch, StateType as SST
from aiomox.mox_client import MoxClient

"""aiomox usage example."""


async def main():
    loop = asyncio.get_running_loop()
    on_con_lost_future = loop.create_future()
    client = MoxClient()
    await client.connect(on_con_lost_future)

    try:
        switch = Switch(0x0000CD17, client, switch_callback)
        dimmer = Dimmer(0x00012D17, client, dimmer_callback)
        shutter = Curtain(0x00019114, client, shutter_callback)

        # let the states sync
        await asyncio.sleep(1)

        # play with switch
        await switch.turn_on()
        await asyncio.sleep(5)
        await switch.turn_off()
        await asyncio.sleep(1)

        # play with the dimmer
        await dimmer.turn_off()
        await asyncio.sleep(5)
        await dimmer.set_luminous(50, 100)
        await asyncio.sleep(5)
        await dimmer.increase(50)
        await asyncio.sleep(5)
        await dimmer.set_luminous(0, 100)
        await asyncio.sleep(5)

        # play with the curtain
        await shutter.set_position(10)
        await asyncio.sleep(10)
        await shutter.set_position(0)
        await asyncio.sleep(10)
        await shutter.set_position(3)
        await asyncio.sleep(10)

        # it's time to stop...
        await client.close()
        await on_con_lost_future
    finally:
        # close the connection in case of an exception
        await client.close()


async def shutter_callback(device: Curtain, state_type: CST) -> None:
    print(f'Curtain callback activated for state type: {state_type}, '
          f'from switch: {hex(device.get_device_id())}, new state: {device.get_position()}')


async def switch_callback(device: Switch, state_type: SST) -> None:
    print(f'Switch callback activated for state type: {state_type}, '
          f'from switch: {hex(device.get_device_id())}, new state: {device.is_on()}')


async def dimmer_callback(device: Dimmer, state_type: DST) -> None:
    print(f'Dimmer callback activated for state type: {state_type}, '
          f'from switch: {hex(device.get_device_id())}, new state: {device.get_luminous()}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
