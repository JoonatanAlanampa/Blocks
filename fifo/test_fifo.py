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
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wdata.value = 0

async def tick(dut):
    await RisingEdge(dut.clk)
    await ReadOnly()
    await NextTimeStep()

@ cocotb.test()
async def first_test(dut):
    cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())

    init_inputs(dut)
    await reset_dut(dut)

    assert int(dut.empty.value) == 1
    assert int(dut.full.value) == 0
    assert int(dut.count.value) == 0

    # Write one byte 0x55 into FIFO
    dut.wr_en.value = 1
    dut.wdata.value = 0x55
    await tick(dut)
    dut.wr_en.value = 0

    assert int(dut.count.value) == 1
    assert int(dut.empty.value) == 0

    # Read one byte
    dut.rd_en.value = 1
    await tick(dut)
    dut.rd_en.value = 0

    assert int(dut.rdata.value) == 0x55
    assert int(dut.count.value) == 0
    assert int(dut.empty.value) == 1

@ cocotb.test()
async def second_test(dut):
    cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())

    init_inputs(dut)
    await reset_dut(dut)

    # Write 4 values
    dut.wr_en.value = 1
    dut.wdata.value = 10
    await tick(dut)
    dut.wdata.value = 20
    await tick(dut)
    dut.wdata.value = 30
    await tick(dut)
    dut.wdata.value = 40
    await tick(dut)

    assert int(dut.full.value) == 1
    assert int(dut.count.value) == 4

    # Write while full
    dut.wdata.value = 7
    await tick(dut)
    dut.wr_en.value = 0

    assert int(dut.count.value) == 4

    # Read out all 4 values
    dut.rd_en.value = 1
    await tick(dut)
    assert int(dut.rdata.value) == 10
    await tick(dut)
    assert int(dut.rdata.value) == 20
    await tick(dut)
    assert int(dut.rdata.value) == 30
    await tick(dut)
    assert int(dut.rdata.value) == 40
    dut.rd_en.value = 0

    assert int(dut.empty.value) == 1
    assert int(dut.count.value) == 0

@cocotb.test()
async def third_test(dut):
    cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())

    init_inputs(dut)
    await reset_dut(dut)

    # Write 2 values
    dut.wr_en.value = 1
    dut.wdata.value = 1
    await tick(dut)
    dut.wdata.value = 2
    await tick(dut)
    assert int(dut.count.value) == 2

    # Simultaneous write and read
    dut.rd_en.value = 1
    dut.wdata.value = 3
    await tick(dut)
    assert int(dut.rdata.value) == 1
    assert int(dut.count.value) == 2
    dut.wr_en.value = 0

    await tick(dut)
    assert int(dut.rdata.value) == 2
    assert int(dut.count.value) == 1
    await tick(dut)
    assert int(dut.rdata.value) == 3
    assert int(dut.count.value) == 0
    dut.rd_en.value = 0

    assert int(dut.empty.value) == 1
    assert int(dut.full.value) == 0