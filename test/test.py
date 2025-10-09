# SPDX-FileCopyrightText: © 2025 Your Name
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_simple_evm(dut):
    """Simple functional test for EVM voting machine"""

    # Clock: 20 ns period => 50 MHz
    cocotb.start_soon(Clock(dut.t_clk, 10, unit="ns").start())  # 10 ns half-period

    # Reset
    dut.t_rst.value = 1
    dut.t_candidate_1.value = 0
    dut.t_candidate_2.value = 0
    dut.t_candidate_3.value = 0
    dut.t_vote_over.value = 0
    await RisingEdge(dut.t_clk)
    await RisingEdge(dut.t_clk)
    dut.t_rst.value = 0

    # === Apply votes ===
    # Candidate 1: 1 vote
    dut.t_candidate_1.value = 1
    await RisingEdge(dut.t_clk)
    dut.t_candidate_1.value = 0
    await RisingEdge(dut.t_clk)

    # Candidate 2: 2 votes
    for _ in range(2):
        dut.t_candidate_2.value = 1
        await RisingEdge(dut.t_clk)
        dut.t_candidate_2.value = 0
        await RisingEdge(dut.t_clk)

    # Candidate 3: 2 votes
    for _ in range(2):
        dut.t_candidate_3.value = 1
        await RisingEdge(dut.t_clk)
        dut.t_candidate_3.value = 0
        await RisingEdge(dut.t_clk)

    # End voting
    dut.t_vote_over.value = 1
    await RisingEdge(dut.t_clk)
    await RisingEdge(dut.t_clk)

    # === Check results ===
    c1 = int(dut.t_result_1.value)
    c2 = int(dut.t_result_2.value)
    c3 = int(dut.t_result_3.value)

    expected = (1, 2, 2)
    actual = (c1, c2, c3)

    dut._log.info(f"Expected votes: C1={expected[0]}, C2={expected[1]}, C3={expected[2]}")
    dut._log.info(f"Actual votes:   C1={c1}, C2={c2}, C3={c3}")

    assert actual == expected, f"Vote counts mismatch! Expected {expected}, got {actual}"

    dut._log.info(" EVM test PASSED!")
