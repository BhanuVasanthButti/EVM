# SPDX-FileCopyrightText: © 2024 Your Name
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_voting_machine_basic(dut):
    """Simple functional test for tt_um_evm top module"""

    # Start the clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # --- Test 1: Switch on EVM ---
    dut.ui_in.value = 0b00001000  # ui_in[3]=1 -> switch_on_evm
    await Timer(50, units="ns")
    assert dut.uo_out.value.integer != 0, "EVM should turn ON"

    # --- Test 2: Candidate 1 vote ---
    dut.ui_in.value = 0b00000001  # vote_candidate_1 = 1
    await Timer(50, units="ns")
    print(f"Candidate 1 vote output: {dut.uo_out.value}")

    # --- Test 3: Display winner ---
    dut.ui_in.value = 0b10000000  # display_winner = 1
    await Timer(50, units="ns")
    print(f"Winner displayed: {dut.uo_out.value}")

    # --- Test 4: Switch off EVM ---
    dut.ui_in.value = 0b01000000  # switch_off_evm = 1
    await Timer(50, units="ns")
    print(f"After switch off: {dut.uo_out.value}")

    # Optional: Example of expected behavior check
    # (modify this according to your internal logic)
    assert dut.uo_out.value.is_resolvable, "Output not driven properly"
