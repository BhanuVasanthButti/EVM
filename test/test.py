# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_evm_voting(dut):
    """Simple functional test for EVM voting machine"""

    # Create 50 MHz clock (20 ns period)
    clock = Clock(dut.clk, 20, units="ns")
    cocotb.start_soon(clock.start())

    dut._log.info("=== Starting EVM Simple Test ===")

    # Reset
    dut.rst.value = 1
    dut.i_candidate_1.value = 0
    dut.i_candidate_2.value = 0
    dut.i_candidate_3.value = 0
    dut.i_voting_over.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 5)

    # Helper: cast one vote (high→low pulse)
    async def cast_vote(candidate):
        if candidate == 1:
            dut.i_candidate_1.value = 1
        elif candidate == 2:
            dut.i_candidate_2.value = 1
        elif candidate == 3:
            dut.i_candidate_3.value = 1
        await ClockCycles(dut.clk, 2)
        # Falling edge triggers vote
        dut.i_candidate_1.value = 0
        dut.i_candidate_2.value = 0
        dut.i_candidate_3.value = 0
        await ClockCycles(dut.clk, 10)  # allow HOLD state to complete
        dut._log.info(f"Vote registered for candidate {candidate}")

    # === Voting Sequence (same as your Verilog TB) ===
    await cast_vote(1)
    await cast_vote(2)
    await cast_vote(1)
    await cast_vote(3)
    await cast_vote(2)
    await cast_vote(2)
    await cast_vote(1)
    await cast_vote(3)

    # === End Voting ===
    dut.i_voting_over.value = 1
    await ClockCycles(dut.clk, 10)

    # === Read Results ===
    c1 = int(dut.o_count1.value)
    c2 = int(dut.o_count2.value)
    c3 = int(dut.o_count3.value)

    dut._log.info("=== Voting Summary ===")
    dut._log.info(f"Candidate 1: {c1}")
    dut._log.info(f"Candidate 2: {c2}")
    dut._log.info(f"Candidate 3: {c3}")

    # === Expected Results ===
    exp1, exp2, exp3 = 3, 3, 2

    if (c1, c2, c3) == (exp1, exp2, exp3):
        dut._log.info("TEST PASSED: Vote counts match expected results!")
    else:
        dut._log.error(f"TEST FAILED: Expected ({exp1},{exp2},{exp3}), got ({c1},{c2},{c3})")
        assert False, "Vote counts do not match expected results"

    dut._log.info("=== Test Completed Successfully ===")
