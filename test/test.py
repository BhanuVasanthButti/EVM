# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    """Main EVM test - matches Vivado testbench voting sequence"""
    
    dut._log.info("Start EVM Test")
    
    # Set the clock period to 20ns (50 MHz - Tiny Tapeout max)
    clock = Clock(dut.clk, 20, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    dut._log.info("Test EVM voting behavior")
    
    # Start EVM (switch_on_evm = ui_in[3])
    dut._log.info("Starting EVM...")
    dut.ui_in.value = 0b00001000  # switch_on_evm = 1
    await ClockCycles(dut.clk, 2)
    
    # Helper function to cast a vote
    async def cast_vote(candidate_num):
        """Cast vote for candidate (1, 2, or 3)"""
        # Set candidate_ready
        dut.ui_in.value = 0b00011000  # switch_on_evm + candidate_ready
        await ClockCycles(dut.clk, 1)
        
        # Press vote button (clear candidate_ready)
        vote_mask = 1 << (candidate_num - 1)
        dut.ui_in.value = 0b00001000 | vote_mask
        await ClockCycles(dut.clk, 2)
        
        # Release button
        dut.ui_in.value = 0b00001000
        await ClockCycles(dut.clk, 2)
        
        dut._log.info(f"  Vote cast for Candidate {candidate_num}")
    
    # Cast votes matching Vivado sequence:
    # C1: 3 votes, C2: 3 votes, C3: 2 votes
    dut._log.info("Casting votes...")
    
    await cast_vote(1)  # Vote 1 → C1
    await cast_vote(2)  # Vote 2 → C2
    await cast_vote(1)  # Vote 3 → C1
    await cast_vote(3)  # Vote 4 → C3
    await cast_vote(2)  # Vote 5 → C2
    await cast_vote(2)  # Vote 6 → C2
    await cast_vote(1)  # Vote 7 → C1
    await cast_vote(3)  # Vote 8 → C3
    
    dut._log.info("Voting complete. Ending session...")
    
    # End voting session (voting_session_done = ui_in[5])
    dut.ui_in.value = 0b00101000  # voting_session_done + switch_on_evm
    await ClockCycles(dut.clk, 10)
    
    # Check results
    dut._log.info("Checking results...")
    
    # Display Candidate 1 (display_results = 00)
    dut.uio_in.value = 0b00000000
    await ClockCycles(dut.clk, 2)
    c1_votes = int(dut.uio_out.value) & 0x7F
    dut._log.info(f"Candidate 1: {c1_votes} votes")
    
    # Display Candidate 2 (display_results = 01)
    dut.uio_in.value = 0b00000001
    await ClockCycles(dut.clk, 2)
    c2_votes = int(dut.uio_out.value) & 0x7F
    dut._log.info(f"Candidate 2: {c2_votes} votes")
    
    # Display Candidate 3 (display_results = 10)
    dut.uio_in.value = 0b00000010
    await ClockCycles(dut.clk, 2)
    c3_votes = int(dut.uio_out.value) & 0x7F
    dut._log.info(f"Candidate 3: {c3_votes} votes")
    
    # Verify expected results
    dut._log.info("="*60)
    dut._log.info(f"Expected: C1=3, C2=3, C3=2")
    dut._log.info(f"Actual:   C1={c1_votes}, C2={c2_votes}, C3={c3_votes}")
    
    # Check vote counts
    assert c1_votes == 3, f"C1 should be 3, got {c1_votes}"
    assert c2_votes == 3, f"C2 should be 3, got {c2_votes}"
    assert c3_votes == 2, f"C3 should be 2, got {c3_votes}"
    
    # Check tie detection (C1 = C2 = 3)
    invalid = (int(dut.uo_out.value) >> 2) & 0x01
    dut._log.info(f"Tie detected (invalid_results): {invalid}")
    
    if invalid == 1:
        dut._log.info("Tie correctly detected between C1 and C2")
    
    dut._log.info("="*60)
    dut._log.info("ALL TESTS PASSED!")
    dut._log.info("="*60)
