import cocotb
import pyuvm
from pyuvm import *

from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly, NextTimeStep, Timer, Combine


class ArbTxn(uvm_sequence_item):
    def __init__(self, name="ArbTxn", src=0, data=0):
        super().__init__(name)
        self.src = int(src)
        self.data = int(data)

    def __eq__(self, other):
        return self.src == other.src and self.data == other.data

    def __repr__(self):
        return f"ArbTxn(src={self.src}, data={self.data})"


class ArbiterBfm:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.dut = cocotb.top

    def init_signals(self):
        self.dut.rst_n.value = 1
        self.dut.in0_valid.value = 0
        self.dut.in0_data.value = 0
        self.dut.in1_valid.value = 0
        self.dut.in1_data.value = 0
        self.dut.out_ready.value = 1

    async def start(self):
        self.init_signals()
        await self.reset()

    async def reset(self):
        self.init_signals()
        self.dut.rst_n.value = 0
        await Timer(2, unit="ns")
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)
        await ReadOnly()
        await NextTimeStep()

    async def cycle(self):
        await RisingEdge(self.dut.clk)
        await ReadOnly()
        await NextTimeStep()

    async def wait_cycles(self, n):
        for _ in range(n):
            await self.cycle()

    def set_out_ready(self, value: int):
        self.dut.out_ready.value = int(bool(value))

    async def send_input(self, channel: int, data: int):
        if channel == 0:
            self.dut.in0_data.value = data
            self.dut.in0_valid.value = 1
        else:
            self.dut.in1_data.value = data
            self.dut.in1_valid.value = 1

        while True:
            # Look at the current cycle, before the next rising edge
            await FallingEdge(self.dut.clk)
            await ReadOnly()

            if channel == 0:
                handshake = int(self.dut.in0_valid.value) and int(self.dut.in0_ready.value)
            else:
                handshake = int(self.dut.in1_valid.value) and int(self.dut.in1_ready.value)

            if handshake:
                break

            await NextTimeStep()

        # Let the actual accepting rising edge happen
        await RisingEdge(self.dut.clk)
        await NextTimeStep()

        if channel == 0:
            self.dut.in0_valid.value = 0
            self.dut.in0_data.value = 0
        else:
            self.dut.in1_valid.value = 0
            self.dut.in1_data.value = 0

    async def wait_for_blocked_output(self):
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()

            if int(self.dut.out_valid.value) == 1 and int(self.dut.out_ready.value) == 0:
                snapshot = (
                    int(self.dut.out_valid.value),
                    int(self.dut.out_data.value),
                    int(self.dut.out_src.value),
                )
                await NextTimeStep()
                return snapshot

            await NextTimeStep()

    async def assert_blocked_output_stable(self, cycles: int, snapshot=None):
        if snapshot is None:
            snapshot = (
                int(self.dut.out_valid.value),
                int(self.dut.out_data.value),
                int(self.dut.out_src.value),
            )

        exp_valid, exp_data, exp_src = snapshot

        for _ in range(cycles):
            await RisingEdge(self.dut.clk)
            await ReadOnly()

            assert int(self.dut.out_valid.value) == exp_valid
            assert int(self.dut.out_data.value) == exp_data
            assert int(self.dut.out_src.value) == exp_src
            assert int(self.dut.out_ready.value) == 0

            await NextTimeStep()

    async def send_both(self, data0: int, data1: int):
        self.dut.in0_data.value = data0
        self.dut.in0_valid.value = 1
        self.dut.in1_data.value = data1
        self.dut.in1_valid.value = 1

        sent0 = False
        sent1 = False

        while not (sent0 and sent1):
            # Sample current-cycle handshakes before the next rising edge
            await FallingEdge(self.dut.clk)
            await ReadOnly()

            do0 = (not sent0) and int(self.dut.in0_valid.value) and int(self.dut.in0_ready.value)
            do1 = (not sent1) and int(self.dut.in1_valid.value) and int(self.dut.in1_ready.value)

            # Let the actual accepting rising edge happen
            await RisingEdge(self.dut.clk)
            await NextTimeStep()

            if do0:
                sent0 = True
                self.dut.in0_valid.value = 0
                self.dut.in0_data.value = 0

            if do1:
                sent1 = True
                self.dut.in1_valid.value = 0
                self.dut.in1_data.value = 0

    async def send_streams_contended(self, values0, values1):
        q0 = list(values0)
        q1 = list(values1)

        # Initially present first item from each side
        if q0:
            self.dut.in0_data.value = q0[0]
            self.dut.in0_valid.value = 1
        else:
            self.dut.in0_data.value = 0
            self.dut.in0_valid.value = 0

        if q1:
            self.dut.in1_data.value = q1[0]
            self.dut.in1_valid.value = 1
        else:
            self.dut.in1_data.value = 0
            self.dut.in1_valid.value = 0

        i0 = 0
        i1 = 0

        while i0 < len(q0) or i1 < len(q1):
            await FallingEdge(self.dut.clk)
            await ReadOnly()

            do0 = (
                i0 < len(q0)
                and int(self.dut.in0_valid.value)
                and int(self.dut.in0_ready.value)
            )
            do1 = (
                i1 < len(q1)
                and int(self.dut.in1_valid.value)
                and int(self.dut.in1_ready.value)
            )

            await RisingEdge(self.dut.clk)
            await NextTimeStep()

            if do0:
                i0 += 1
                if i0 < len(q0):
                    self.dut.in0_data.value = q0[i0]
                    self.dut.in0_valid.value = 1
                else:
                    self.dut.in0_data.value = 0
                    self.dut.in0_valid.value = 0

            if do1:
                i1 += 1
                if i1 < len(q1):
                    self.dut.in1_data.value = q1[i1]
                    self.dut.in1_valid.value = 1
                else:
                    self.dut.in1_data.value = 0
                    self.dut.in1_valid.value = 0


class InputSeq(uvm_sequence):
    def __init__(self, name="InputSeq", src=0, values=None):
        super().__init__(name)
        self.src = int(src)
        self.values = list(values or [])

    async def body(self):
        for value in self.values:
            txn = ArbTxn("txn", src=self.src, data=value)
            await self.start_item(txn)
            await self.finish_item(txn)


class InDriver(uvm_driver):
    def __init__(self, name, parent, channel):
        super().__init__(name, parent)
        self.channel = int(channel)

    def start_of_simulation_phase(self):
        self.bfm = ArbiterBfm()

    async def run_phase(self):
        while True:
            txn = await self.seq_item_port.get_next_item()
            await self.bfm.send_input(self.channel, txn.data)
            self.seq_item_port.item_done()


class OutMonitor(uvm_component):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        dut = cocotb.top
        while True:
            # Sample the transaction during the cycle before the accepting rising edge
            await FallingEdge(dut.clk)
            await ReadOnly()

            if int(dut.out_valid.value) == 1 and int(dut.out_ready.value) == 1:
                txn = ArbTxn(
                    "observed",
                    src=int(dut.out_src.value),
                    data=int(dut.out_data.value),
                )
                self.ap.write(txn)

            await NextTimeStep()


class Scoreboard(uvm_subscriber):
    def build_phase(self):
        self.expected = []
        self.observed = []

    def write(self, txn):
        self.observed.append(ArbTxn("obs_copy", src=txn.src, data=txn.data))

    def check_phase(self):
        assert len(self.observed) == len(self.expected), (
            f"Observed {len(self.observed)} items, expected {len(self.expected)}\n"
            f"Observed: {self.observed}\nExpected: {self.expected}"
        )

        for i, (exp, obs) in enumerate(zip(self.expected, self.observed)):
            assert exp == obs, f"Mismatch at index {i}: expected {exp}, got {obs}"


class ArbEnv(uvm_env):
    def build_phase(self):
        self.seqr0 = uvm_sequencer("seqr0", self)
        self.seqr1 = uvm_sequencer("seqr1", self)

        self.drv0 = InDriver("drv0", self, channel=0)
        self.drv1 = InDriver("drv1", self, channel=1)

        self.mon = OutMonitor("mon", self)
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.drv0.seq_item_port.connect(self.seqr0.seq_item_export)
        self.drv1.seq_item_port.connect(self.seqr1.seq_item_export)
        self.mon.ap.connect(self.scoreboard.analysis_export)


class BaseTest(uvm_test):
    def build_phase(self):
        self.env = ArbEnv("env", self)

    async def start_test(self):
        self.raise_objection()

        cocotb.start_soon(Clock(cocotb.top.clk, 2, unit="ns").start())

        self.bfm = ArbiterBfm()
        await self.bfm.start()

    async def wait_for_expected(self, timeout_cycles=50):
        cycles = 0
        while len(self.env.scoreboard.observed) < len(self.env.scoreboard.expected):
            await self.bfm.cycle()
            cycles += 1
            assert cycles < timeout_cycles, (
                f"Timeout waiting for observations.\n"
                f"Observed: {self.env.scoreboard.observed}\n"
                f"Expected: {self.env.scoreboard.expected}"
            )

        await self.bfm.wait_cycles(2)
        self.drop_objection()


@pyuvm.test()
class Ch0OnlyTest(BaseTest):
    async def run_phase(self):
        await self.start_test()

        self.env.scoreboard.expected = [
            ArbTxn("exp0", 0, 11),
            ArbTxn("exp1", 0, 22),
            ArbTxn("exp2", 0, 33),
        ]

        seq0 = InputSeq("seq0", src=0, values=[11, 22, 33])
        await seq0.start(self.env.seqr0)

        await self.wait_for_expected()


@pyuvm.test()
class Ch1OnlyTest(BaseTest):
    async def run_phase(self):
        await self.start_test()

        self.env.scoreboard.expected = [
            ArbTxn("exp0", 1, 11),
            ArbTxn("exp1", 1, 22),
            ArbTxn("exp2", 1, 33),
        ]

        seq1 = InputSeq("seq1", src=1, values=[11, 22, 33])
        await seq1.start(self.env.seqr1)

        await self.wait_for_expected()


@pyuvm.test()
class FairnessTest(BaseTest):
    async def run_phase(self):
        await self.start_test()

        self.env.scoreboard.expected = [
            ArbTxn("e0", 0, 10),
            ArbTxn("e1", 1, 11),
            ArbTxn("e2", 0, 20),
            ArbTxn("e3", 1, 21),
            ArbTxn("e4", 0, 30),
            ArbTxn("e5", 1, 31),
        ]

        await self.bfm.send_streams_contended([10, 20, 30], [11, 21, 31])

        await self.wait_for_expected()


@pyuvm.test()
class BackpressureHoldTest(BaseTest):
    async def run_phase(self):
        await self.start_test()

        self.env.scoreboard.expected = [
            ArbTxn("exp0", 0, 0xA5),
        ]

        self.bfm.set_out_ready(0)

        seq0 = InputSeq("seq0", src=0, values=[0xA5])
        seq_task = cocotb.start_soon(seq0.start(self.env.seqr0))

        snapshot = await self.bfm.wait_for_blocked_output()
        assert snapshot == (1, 0xA5, 0), f"Unexpected blocked output snapshot: {snapshot}"

        await self.bfm.assert_blocked_output_stable(cycles=3, snapshot=snapshot)

        self.bfm.set_out_ready(1)

        await seq_task
        await self.wait_for_expected()