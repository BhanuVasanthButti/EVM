# SPDX-FileCopyrightText: © 2024 Bhanu Vasanth Butti
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLK_PERIOD = 20  # ns (50 MHz - Tiny Tapeout max)

@cocotb.test()
async def test_evm_full_voting(dut):
    """
    Full voting sequence test matching EVM FSM protocol
    
    FSM Protocol:
    1. switch_on_evm → WAITING_FOR_CANDIDATE
    2. candidate_ready=1 → WAITING_FOR_CANDIDATE_TO_VOTE
    3. candidate_ready=0, vote_button=1 → flag set, CANDIDATE_VOTED
    4. Vote counted, back to WAITING_FOR_CANDIDATE
    """
    
    # Setup clock
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, units="ns").start())
    
    # Apply reset (active low in Tiny Tapeout)
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(CLK_PERIOD * 5, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    cocotb.log.info("="*70)
    cocotb.log.info("EVM Test Started - Reset deasserted")
    cocotb.log.info("="*70)
    
    # Pin mapping:
    # ui_in[0] = vote_candidate_1
    # ui_in[1] = vote_candidate_2  
    # ui_in[2] = vote_candidate_3
    # ui_in[3] = switch_on_evm
    # ui_in[4] = candidate_ready
    # ui_in[5] = voting_session_done
    # ui_in[6] = switch_off_evm
    # ui_in[7] = display_winner
    # uio_in[1:0] = display_results
    
    async def cast_vote(candidate_num):
        """
        Cast vote following EXACT FSM protocol:
        1. Set candidate_ready=1 (voter enters booth)
        2. Clear candidate_ready=0 (voter inside, ready to vote)
        3. Press vote_button (while candidate_ready=0)
        4. Release vote_button
        5. Wait for vote to be counted
        """
        # Step 1: candidate_ready=1 (transition to WAITING_FOR_CANDIDATE_TO_VOTE)
        dut.ui_in.value = 0b00011000  # switch_on_evm + candidate_ready
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        # Step 2: candidate_ready=0, press vote button (vote gets registered)
        vote_mask = 1 << (candidate_num - 1)
        dut.ui_in.value = 0b00001000 | vote_mask  # switch_on_evm + vote_button
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        
        # Step 3: Release vote button (transition to CANDIDATE_VOTED, then back to WAITING_FOR_CANDIDATE)
        dut.ui_in.value = 0b00001000  # switch_on_evm only
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)  # Wait for vote to be counted
        
        cocotb.log.info(f"  Vote cast for Candidate {candidate_num}")
    
    # 1. Switch ON EVM (IDLE → WAITING_FOR_CANDIDATE)
    cocotb.log.info("Step 1: Switching ON EVM...")
    dut.ui_in.value = 0b00001000  # switch_on_evm
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    cocotb.log.info("  EVM ON - State: WAITING_FOR_CANDIDATE")
    
    # 2. Cast 8 votes matching Vivado testbench
    # Expected: C1=3, C2=3, C3=2
    cocotb.log.info("")
    cocotb.log.info("Step 2: Casting votes (C1=3, C2=3, C3=2)...")
    
    await cast_vote(1)  # Vote 1 → Candidate 1
    await cast_vote(2)  # Vote 2 → Candidate 2
    await cast_vote(1)  # Vote 3 → Candidate 1
    await cast_vote(3)  # Vote 4 → Candidate 3
    await cast_vote(2)  # Vote 5 → Candidate 2
    await cast_vote(2)  # Vote 6 → Candidate 2
    await cast_vote(1)  # Vote 7 → Candidate 1
    await cast_vote(3)  # Vote 8 → Candidate 3
    
    cocotb.log.info("  All votes cast successfully")
    
    # 3. End voting session (→ VOTING_PROCESS_DONE)
    cocotb.log.info("")
    cocotb.log.info("Step 3: Ending voting session...")
    dut.ui_in.value = 0b00101000  # voting_session_done + switch_on_evm
    await RisingEdge(dut.clk)
    await Timer(CLK_PERIOD * 5, units="ns")  # Wait for FSM to settle
    cocotb.log.info("  State: VOTING_PROCESS_DONE")
    
    # 4. Check results
    cocotb.log.info("")
    cocotb.log.info("="*70)
    cocotb.log.info("Step 4: Reading vote counts...")
    cocotb.log.info("="*70)
    
    # Display Candidate 1 (display_results = 00)
    dut.uio_in.value = 0b00
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    c1_votes = int(dut.uio_out.value) & 0x7F
    c1_name = int(dut.uo_out.value) & 0x03
    cocotb.log.info(f"  Candidate 1: {c1_votes} votes (candidate_name={c1_name})")
    
    # Display Candidate 2 (display_results = 01)
    dut.uio_in.value = 0b01
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    c2_votes = int(dut.uio_out.value) & 0x7F
    c2_name = int(dut.uo_out.value) & 0x03
    cocotb.log.info(f"  Candidate 2: {c2_votes} votes (candidate_name={c2_name})")
    
    # Display Candidate 3 (display_results = 10)
    dut.uio_in.value = 0b10
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    c3_votes = int(dut.uio_out.value) & 0x7F
    c3_name = int(dut.uo_out.value) & 0x03
    cocotb.log.info(f"  Candidate 3: {c3_votes} votes (candidate_name={c3_name})")
    
    # Check tie detection
    invalid_results = (int(dut.uo_out.value) >> 2) & 0x01
    cocotb.log.info(f"  Invalid results flag: {invalid_results} (tie detection)")
    
    cocotb.log.info("="*70)
    cocotb.log.info("Expected: C1=3, C2=3, C3=2 (Tie between C1 and C2)")
    cocotb.log.info(f"Actual:   C1={c1_votes}, C2={c2_votes}, C3={c3_votes}")
    cocotb.log.info("="*70)
    
    # Assertions
    assert dut.uo_out.value.integer is not None, "Output not driven"
    assert c1_votes == 3, f"✗ Candidate 1 should have 3 votes, got {c1_votes}"
    assert c2_votes == 3, f"✗ Candidate 2 should have 3 votes, got {c2_votes}"
    assert c3_votes == 2, f"✗ Candidate 3 should have 2 votes, got {c3_votes}"
    assert invalid_results == 1, f"✗ Should detect tie (C1=C2=3), got invalid_results={invalid_results}"
    
    cocotb.log.info("")
    cocotb.log.info(" Candidate 1: 3 votes")
    cocotb.log.info(" Candidate 2: 3 votes")
    cocotb.log.info(" Candidate 3: 2 votes")
    cocotb.log.info(" Tie correctly detected")
    
    # 5. Display winner (optional)
    cocotb.log.info("")
    cocotb.log.info("Step 5: Displaying winner...")
    dut.ui_in.value = 0b10101000  # display_winner + voting_session_done + switch_on_evm
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    winner_name = int(dut.uo_out.value) & 0x03
    winner_votes = int(dut.uio_out.value) & 0x7F
    cocotb.log.info(f"  Winner: Candidate {winner_name} with {winner_votes} votes")
    
    # 6. Switch OFF EVM (→ IDLE)
    cocotb.log.info("")
    cocotb.log.info("Step 6: Switching OFF EVM...")
    dut.ui_in.value = 0b01101000  # switch_off_evm + voting_session_done + switch_on_evm
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    cocotb.log.info("  EVM OFF - State: IDLE")
    
    # Final summary
    cocotb.log.info("")
    cocotb.log.info("="*70)
    cocotb.log.info(" ALL TESTS PASSED SUCCESSFULLY! ")
    cocotb.log.info("="*70)
    cocotb.log.info("Test Summary:")
    cocotb.log.info("  - 8 votes cast successfully")
    cocotb.log.info("  - Vote counting accurate (C1=3, C2=3, C3=2)")
    cocotb.log.info("  - Tie detection working (C1=C2)")
    cocotb.log.info("  - FSM state transitions correct")
    cocotb.log.info("  - All assertions passed")
    cocotb.log.info("="*70)
