import asyncio

from openrover import find_openrover
from openrover_data import OpenRoverFirmwareVersion
from protocol import OpenRoverPacketizer, SerialConnectionContext
from unasync_decorator import unasync

port = asyncio.get_event_loop().run_until_complete(find_openrover())
n = 1000


@unasync
async def test_packetizer_read_write_immediate():
    n_received = 0

    async with SerialConnectionContext(port) as (reader, writer):
        packetizer = OpenRoverPacketizer(reader, writer)
        for i in range(n):
            packetizer.write(0, 0, 0, 10, 40)
            try:
                key, version = await asyncio.wait_for(packetizer._read(), timeout=1)
                assert key == 40
                assert isinstance(version, OpenRoverFirmwareVersion)
                assert isinstance(version.value, int)
                assert 0 < version.value
                n_received += 1
            except asyncio.TimeoutError:
                pass
    print(f'success ratio {n_received / n}')
    assert 0.9 < n_received / n <= 1


@unasync
async def test_packetizer_writes_then_reads():
    n_received = 0

    async with SerialConnectionContext(port) as (reader, writer):
        packetizer = OpenRoverPacketizer(reader, writer)
        for i in range(n):
            packetizer.write(0, 0, 0, 10, 40)
        for i in range(n):
            try:
                key, version = await asyncio.wait_for(packetizer._read(), timeout=0.2)
                assert key == 40
                assert isinstance(version, OpenRoverFirmwareVersion)
                assert isinstance(version.value, int)
                assert 0 < version.value
                n_received += 1
            except asyncio.TimeoutError:
                break
    print(f'success ratio {n_received / n}')
    assert 0.9 < n_received / n <= 1


async def write_packets(packetizer):
    for i in range(n):
        packetizer.write(0, 0, 0, 10, 40)
        await asyncio.sleep(0)


async def read_packets(packetizer):
    n_received = 0
    async for key, version in packetizer.read_many(n, item_timeout=0.2):
        assert key == 40
        assert isinstance(version, OpenRoverFirmwareVersion)
        assert isinstance(version.value, int)
        assert 0 < version.value
        n_received += 1
    return n_received


@unasync
async def test_packetizer_write_read_full_async():
    async with SerialConnectionContext(port) as (reader, writer):
        packetizer = OpenRoverPacketizer(reader, writer)

        write_packets_task = asyncio.ensure_future(write_packets(packetizer))
        read_packets_task = asyncio.ensure_future(read_packets(packetizer))

        await asyncio.gather(read_packets_task, write_packets_task)
        n_received = read_packets_task.result()

    print(f'success ratio {n_received / n}')
    assert 0.9 < n_received / n <= 1
