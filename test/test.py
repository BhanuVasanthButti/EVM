# SPDX-FileCopyrightText: © 2024 Bhanu Vasanth Butti
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

# Pin mapping for tt_um_evm wrapper:
# ui_in[0] = vote_candidate_1
# ui_in[1] = vote_candidate_2
# ui_in[2] = vote_candidate_3
# ui_in[3] = switch_on_evm
# ui_in[4] = candidate_ready
# ui_in[5] = voting_session_done (vote_over)
# ui_in[6] = switch_off_evm
# ui_in[7] = display_winner
#
# uio_in[1:0] = display_results
#
# uo_out[1:0] = candidate_name
# uo_out[2] = invalid_results
# uo_out[3] = voting_in_progress
# uo_out[4] = voting_done
#
# uio_out[6:0] = results (vote count)

@cocotb.test()
async def test_voting_machine(dut):
    """
    EVM Test matching Vivado testbench timing
    Clock: 50MHz (20ns period) - Tiny Tapeout maximum
    Timing: Matches original Vivado testbench sequence
    """
    
    dut._log.info("="*70)
    dut._log.info("Starting EVM Test - Matching Vivado Testbench")
    dut._log.info("="*70)
    
    # Clock setup: 50MHz = 20ns period (Tiny Tapeout max frequency)
    clock = Clock(dut.clk, 20, units="ns")
    cocotb.start_soon(clock.start())
    
    # Helper function to set vote button
    def set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0):
        """Set vote buttons while maintaining other signals"""
        # Keep switch_on_evm active after initial start
        base = 0b00001000  # switch_on_evm always on during voting
        if vote_over:
            base |= 0b00100000  # voting_session_done
        value = base | (c1 << 0) | (c2 << 1) | (c3 << 2)
        dut.ui_in.value = value
    
    # Helper function to display results
    def display_candidate_result(candidate_num):
        """Set display_results to show specific candidate"""
        dut.uio_in.value = candidate_num & 0x03
    
    # Initialize all inputs (time = 0)
    dut._log.info("Time = 0ns: Initializing inputs")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 1  # Active LOW - keep high initially
    
    # Apply reset (matching Vivado: t_rst = 1'b1 initially)
    dut._log.info("Time = 0ns: Applying reset (rst_n = 0)")
    dut.rst_n.value = 0  # Assert reset (active low)
    
    # Wait 20ns (matching Vivado: #20 t_rst = 1'b0)
    await Timer(20, units="ns")
    
    # Release reset and start EVM
    dut._log.info("Time = 20ns: Releasing reset, starting EVM")
    dut.rst_n.value = 1  # De-assert reset
    set_vote_buttons(0, 0, 0, 0)
    dut.ui_in.value = 0b00001000  # switch_on_evm = 1
    
    # Wait 10ns (matching Vivado: #10 before first vote)
    await Timer(10, units="ns")
    
    # Time = 30ns: Vote 1 for Candidate 1 - PRESS
    dut._log.info("Time = 30ns: Candidate 1 button pressed")
    set_vote_buttons(c1=1, c2=0, c3=0, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 40ns: Vote 1 for Candidate 1 - RELEASE
    dut._log.info("Time = 40ns: Candidate 1 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(20, units="ns")
    
    # Time = 60ns: Vote 2 for Candidate 2 - PRESS
    dut._log.info("Time = 60ns: Candidate 2 button pressed")
    set_vote_buttons(c1=0, c2=1, c3=0, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 70ns: Vote 2 for Candidate 2 - RELEASE
    dut._log.info("Time = 70ns: Candidate 2 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(20, units="ns")
    
    # Time = 90ns: Vote 3 for Candidate 1 - PRESS
    dut._log.info("Time = 90ns: Candidate 1 button pressed")
    set_vote_buttons(c1=1, c2=0, c3=0, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 100ns: Vote 3 for Candidate 1 - RELEASE
    dut._log.info("Time = 100ns: Candidate 1 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(20, units="ns")
    
    # Time = 120ns: Vote 4 for Candidate 3 - PRESS
    dut._log.info("Time = 120ns: Candidate 3 button pressed")
    set_vote_buttons(c1=0, c2=0, c3=1, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 130ns: Vote 4 for Candidate 3 - RELEASE
    dut._log.info("Time = 130ns: Candidate 3 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(20, units="ns")
    
    # Time = 150ns: Vote 5 for Candidate 2 - PRESS
    dut._log.info("Time = 150ns: Candidate 2 button pressed")
    set_vote_buttons(c1=0, c2=1, c3=0, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 160ns: Vote 5 for Candidate 2 - RELEASE
    dut._log.info("Time = 160ns: Candidate 2 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(20, units="ns")
    
    # Time = 180ns: Vote 6 for Candidate 2 - PRESS
    dut._log.info("Time = 180ns: Candidate 2 button pressed")
    set_vote_buttons(c1=0, c2=1, c3=0, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 190ns: Vote 6 for Candidate 2 - RELEASE
    dut._log.info("Time = 190ns: Candidate 2 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(20, units="ns")
    
    # Time = 210ns: Vote 7 for Candidate 1 - PRESS
    dut._log.info("Time = 210ns: Candidate 1 button pressed")
    set_vote_buttons(c1=1, c2=0, c3=0, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 220ns: Vote 7 for Candidate 1 - RELEASE
    dut._log.info("Time = 220ns: Candidate 1 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(20, units="ns")
    
    # Time = 240ns: Vote 8 for Candidate 3 - PRESS
    dut._log.info("Time = 240ns: Candidate 3 button pressed")
    set_vote_buttons(c1=0, c2=0, c3=1, vote_over=0)
    await Timer(10, units="ns")
    
    # Time = 250ns: Vote 8 for Candidate 3 - RELEASE
    dut._log.info("Time = 250ns: Candidate 3 button released (Vote registered)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=0)
    await Timer(30, units="ns")
    
    # Time = 280ns: End voting session
    dut._log.info("Time = 280ns: Asserting voting_over (voting_session_done)")
    set_vote_buttons(c1=0, c2=0, c3=0, vote_over=1)
    await Timer(50, units="ns")
    
    # Time = 330ns: Check results
    dut._log.info("="*70)
    dut._log.info("Time = 330ns: Checking vote counts")
    dut._log.info("="*70)
    
    # Display Candidate 1 results
    display_candidate_result(0)  # display_results = 00
    await Timer(20, units="ns")
    c1_votes = int(dut.uio_out.value) & 0x7F
    c1_name = int(dut.uo_out.value) & 0x03
    dut._log.info(f"Candidate 1: {c1_votes} votes (candidate_name: {c1_name})")
    
    # Display Candidate 2 results
    display_candidate_result(1)  # display_results = 01
    await Timer(20, units="ns")
    c2_votes = int(dut.uio_out.value) & 0x7F
    c2_name = int(dut.uo_out.value) & 0x03
    dut._log.info(f"Candidate 2: {c2_votes} votes (candidate_name: {c2_name})")
    
    # Display Candidate 3 results
    display_candidate_result(2)  # display_results = 10
    await Timer(20, units="ns")
    c3_votes = int(dut.uio_out.value) & 0x7F
    c3_name = int(dut.uo_out.value) & 0x03
    dut._log.info(f"Candidate 3: {c3_votes} votes (candidate_name: {c3_name})")
    
    dut._log.info("="*70)
    dut._log.info("Expected Results:")
    dut._log.info("  Candidate 1: 3 votes")
    dut._log.info("  Candidate 2: 3 votes")
    dut._log.info("  Candidate 3: 2 votes")
    dut._log.info("="*70)
    
    # Verify vote counts
    assert c1_votes == 3, f"Candidate 1 should have 3 votes, got {c1_votes}"
    assert c2_votes == 3, f"Candidate 2 should have 3 votes, got {c2_votes}"
    assert c3_votes == 2, f"Candidate 3 should have 2 votes, got {c3_votes}"
    
    # Check for tie condition (C1 = C2 = 3)
    invalid = (int(dut.uo_out.value) >> 2) & 0x01
    dut._log.info(f"Invalid results flag: {invalid} (Expected: 1 for tie)")
    assert invalid == 1, f"Should detect tie (C1=C2), invalid_results should be 1, got {invalid}"
    
    # Time = 390ns: Reset after voting over (matching Vivado: #50 t_rst = 1'b1)
    await Timer(50, units="ns")
    dut._log.info("Time = 440ns: Applying final reset")
    dut.rst_n.value = 0
    await Timer(60, units="ns")
    
    # Final verification
    dut._log.info("="*70)
    dut._log.info("✓ TEST PASSED - All vote counts match expected values!")
    dut._log.info("  - Candidate 1: 3 votes ✓")
    dut._log.info("  - Candidate 2: 3 votes ✓")
    dut._log.info("  - Candidate 3: 2 votes ✓")
    dut._log.info("  - Tie detected: YES ✓")
    dut._log.info("="*70)
    dut._log.info("Time = 500ns: Test completed successfully!")
    dut._log.info("="*70)


@cocotb.test()
async def test_evm_timing_summary(dut):
    """Quick summary test showing the voting sequence"""
    
    dut._log.info("="*70)
    dut._log.info("EVM VOTING SEQUENCE SUMMARY")
    dut._log.info("="*70)
    dut._log.info("Clock: 50MHz (20ns period)")
    dut._log.info("Reset: Active LOW (rst_n)")
    dut._log.info("")
    dut._log.info("Voting Sequence:")
    dut._log.info("  Time = 30-40ns:   Vote 1 → Candidate 1")
    dut._log.info("  Time = 60-70ns:   Vote 2 → Candidate 2")
    dut._log.info("  Time = 90-100ns:  Vote 3 → Candidate 1")
    dut._log.info("  Time = 120-130ns: Vote 4 → Candidate 3")
    dut._log.info("  Time = 150-160ns: Vote 5 → Candidate 2")
    dut._log.info("  Time = 180-190ns: Vote 6 → Candidate 2")
    dut._log.info("  Time = 210-220ns: Vote 7 → Candidate 1")
    dut._log.info("  Time = 240-250ns: Vote 8 → Candidate 3")
    dut._log.info("")
    dut._log.info("Final Tally:")
    dut._log.info("  Candidate 1: 3 votes")
    dut._log.info("  Candidate 2: 3 votes (TIE)")
    dut._log.info("  Candidate 3: 2 votes")
    dut._log.info("="*70)
    
    # This test just prints the summary, main test does the actual verification
    await Timer(1, units="ns")
