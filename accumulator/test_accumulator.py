import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly, NextTimeStep


async def reset_dut(dut, duration_ns=10):
    dut.rst_n.value = 0
    await Timer(duration_ns, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    await NextTimeStep()


def init_inputs(dut):
    dut.rst_n.value = 1
    dut.clear.value = 0
    dut.load_en.value = 0
    dut.add_en.value = 0
    dut.load_data.value = 0
    dut.add_data.value = 0


async def tick(dut):
    await RisingEdge(dut.clk)
    await ReadOnly()
    await NextTimeStep()


@ cocotb.test()
async def first_test(dut):
    cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())

    init_inputs(dut)
    await reset_dut(dut)

    assert int(dut.sum.value) == 0
    assert int(dut.overflow.value) == 0

    # Load 42
    dut.load_en.value = 1
    dut.load_data.value =42
    await tick(dut)

    assert int(dut.sum.value) == 42
    assert int(dut.overflow.value) == 0

    dut.load_en.value = 0

    # Clear
    dut.clear.value = 1
    await tick(dut)

    assert int(dut.sum.value) == 0
    assert int(dut.overflow.value) == 0

    dut.clear.value = 0


@cocotb.test()
async def second_test(dut):
    cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())

    init_inputs(dut)
    await reset_dut(dut)

    # Load 250
    dut.load_en.value = 1
    dut.load_data.value = 250
    await tick(dut)

    assert int(dut.sum.value) == 250
    assert int(dut.overflow.value) == 0

    dut.load_en.value = 0

    # Add 10 -> wrap to 4, overflow pulse = 1
    dut.add_en.value = 1
    dut.add_data.value = 10
    await tick(dut)

    assert int(dut.sum.value) == 4
    assert int(dut.overflow.value) == 1

    # Stop adding, overflow should drop next cycle
    dut.add_en.value = 0
    await tick(dut)

    assert int(dut.sum.value) == 4
    assert int(dut.overflow.value) == 0

    # Priority: clear beats load
    dut.clear.value = 1
    dut.load_en.value = 1
    dut.load_data.value = 99
    await tick(dut)

    assert int(dut.sum.value) == 0
    assert int(dut.overflow.value) == 0

    dut.clear.value = 0
    dut.load_en.value = 0