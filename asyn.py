import asyncio
import logging

from pymodbus.client.async.tcp import AsyncModbusTCPClient as ModbusClient

from pymodbus.client.async import schedulers


from threading import Thread
import time


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


UNIT = 0x01


async def start_async_test(client):
  
    log.debug("Reading Coils")
    rr = await client.read_coils(1, 1, unit=0x01)
    log.debug("Write to a Coil and read back")
    rq = await client.write_coil(0, True, unit=UNIT)
    rr = await client.read_coils(0, 1, unit=UNIT)
    assert(rq.function_code < 0x80)     # test that we are not an error
    assert(rr.bits[0] == True)          # test the expected value

    log.debug("Write to multiple coils and read back- test 1")
    rq = await client.write_coils(1, [True]*8, unit=UNIT)
    assert(rq.function_code < 0x80)     # test that we are not an error
    rr = await client.read_coils(1, 21, unit=UNIT)
    assert(rr.function_code < 0x80)     # test that we are not an error
    resp = [True]*8

    resp.extend([False]*16)
    log.debug(rr.bits)
    assert(rr.bits == resp)         # test the expected value

    log.debug("Write to multiple coils and read back - test 2")
    rq = await client.write_coils(1, [False]*8, unit=UNIT)
    rr = await client.read_coils(1, 8, unit=UNIT)
    assert(rq.function_code < 0x80)     # test that we are not an error
    assert(rr.bits == [False]*8)         # test the expected value

    log.debug("Read discrete inputs")
    rr = await client.read_discrete_inputs(0, 8, unit=UNIT)
    assert(rq.function_code < 0x80)     # test that we are not an error

    log.debug("Write to a holding register and read back")
    rq = await client.write_register(1, 10, unit=UNIT)
    rr = await client.read_holding_registers(1, 1, unit=UNIT)
    assert(rq.function_code < 0x80)     # test that we are not an error
    assert(rr.registers[0] == 10)       # test the expected value

    log.debug("Write to multiple holding registers and read back")
    rq = await client.write_registers(1, [10]*8, unit=UNIT)
    rr = await client.read_holding_registers(1, 8, unit=UNIT)
    assert(rq.function_code < 0x80)     # test that we are not an error
    assert(rr.registers == [10]*8)      # test the expected value

    log.debug("Read input registers")
    rr = await client.read_input_registers(1, 8, unit=UNIT)
    assert(rq.function_code < 0x80)     # test that we are not an error

    arguments = {
        'read_address':    1,
        'read_count':      8,
        'write_address':   1,
        'write_registers': [20]*8,
    }
    log.debug("Read write registeres simulataneously")
    rq = await client.readwrite_registers(unit=UNIT, **arguments)
    rr = await client.read_holding_registers(1, 8, unit=UNIT)
    # assert(rq.function_code < 0x80)     # test that we are not an error
    assert(rq.registers == [20]*8)      # test the expected value
    assert(rr.registers == [20]*8)      # test the expected value
    await asyncio.sleep(1)


def run_with_not_running_loop():
    """
    A loop is created and is passed to ModbusClient factory to be used.

    :return:
    """
    log.debug("Running Async client with asyncio loop not yet started")
    log.debug("------------------------------------------------------")
    loop = asyncio.new_event_loop()
    assert not loop.is_running()
    new_loop, client = ModbusClient(schedulers.ASYNC_IO, port=502, loop=loop)
    loop.run_until_complete(start_async_test(client.protocol))
    loop.close()
    log.debug("--------------RUN_WITH_NOT_RUNNING_LOOP---------------")
    log.debug("")


def run_with_already_running_loop():
    """
    An already running loop is passed to ModbusClient Factory
    :return:
    """
    log.debug("Running Async client with asyncio loop already started")
    log.debug("------------------------------------------------------")

    def done(future):
        log.info("Done !!!")

    def start_loop(loop):
        """
        Start Loop
        :param loop:
        :return:
        """
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    t = Thread(target=start_loop, args=[loop])
    t.daemon = True
    # Start the loop
    t.start()
    assert loop.is_running()
    asyncio.set_event_loop(loop)
    loop, client = ModbusClient(schedulers.ASYNC_IO, port=502, loop=loop)
    future = asyncio.run_coroutine_threadsafe(
        start_async_test(client.protocol), loop=loop)
    future.add_done_callback(done)
    while not future.done():
        time.sleep(0.1)
    loop.stop()
    log.debug("--------DONE RUN_WITH_ALREADY_RUNNING_LOOP-------------")
    log.debug("")


def run_with_no_loop():
    loop, client = ModbusClient(schedulers.ASYNC_IO, port=502)
    loop.run_until_complete(start_async_test(client.protocol))
    loop.close()


if __name__ == '__main__':
    # Run with No loop
    log.debug("Running Async client")
    log.debug("------------------------------------------------------")
    # run_with_no_loop()
    log.debug("1.) Started run_with_no_loop()")
    # Run with loop not yet started
    run_with_not_running_loop()

    log.debug("2.) Started run_with_not_running_loop()")

    # Run with already running loop
    run_with_already_running_loop()

    log.debug("3.) Started run_with_already_running_loop()")
    log.debug("---------------------RUN_WITH_NO_LOOP-----------------")
    log.debug("")