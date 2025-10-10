# SPDX-FileCopyrightText: © 2024 Bhanu Vasanth Butti
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLK_PERIOD = 20  # ns (50 MHz)

@cocotb.test()
async def test_project(dut):
    """
    EVM test with extensive logging for debugging
    """
    
    dut._log.info("="*70)
    dut._log.info("STARTING EVM TEST")
    dut._log.info("="*70)
    
    # Setup clock
    clock = Clock(dut.clk, CLK_PERIOD, units="ns")
    cocotb.start_soon(clock.start())
    dut._log.info("✓ Clock started (50MHz)")
    
    # Apply reset
    dut._log.info("Applying reset...")
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(100, units="ns")
    
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut._log.info("✓ Reset released")
    
    async def cast_vote_safe(candidate_num):
        """Cast vote with error handling"""
        try:
            dut._log.info(f"  Casting vote for Candidate {candidate_num}...")
            
            # Step 1: candidate_ready=1
            dut.ui_in.value = 0b00011000
            await RisingEdge(dut.clk)
            dut._log.info(f"    - candidate_ready set")
            
            # Step 2: vote button + candidate_ready=0
            vote_mask = 1 << (candidate_num - 1)
            dut.ui_in.value = 0b00001000 | vote_mask
            await RisingEdge(dut.clk)
            await RisingEdge(dut.clk)
            dut._log.info(f"    - Vote button pressed")
            
            # Step 3: Release
            dut.ui_in.value = 0b00001000
            await RisingEdge(dut.clk)
            await RisingEdge(dut.clk)
            await RisingEdge(dut.clk)
            dut._log.info(f"  ✓ Vote {candidate_num} complete")
            
        except Exception as e:
            dut._log.error(f"ERROR in cast_vote: {e}")
            raise
    
    try:
        # 1. Switch ON EVM
        dut._log.info("")
        dut._log.info("Step 1: Switching ON EVM...")
        dut.ui_in.value = 0b00001000
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut._log.info("✓ EVM switched ON")
        
        # 2. Cast votes
        dut._log.info("")
        dut._log.info("Step 2: Casting 8 votes...")
        await cast_vote_safe(1)  # C1
        await cast_vote_safe(2)  # C2
        await cast_vote_safe(1)  # C1
        await cast_vote_safe(3)  # C3
        await cast_vote_safe(2)  # C2
        await cast_vote_safe(2)  # C2
        await cast_vote_safe(1)  # C1
        await cast_vote_safe(3)  # C3
        dut._log.info("✓ All 8 votes cast")
        
        # 3. End voting
        dut._log.info("")
        dut._log.info("Step 3: Ending voting session...")
        dut.ui_in.value = 0b00101000
        await RisingEdge(dut.clk)
        await Timer(100, units="ns")
        dut._log.info("✓ Voting session ended")
        
        # 4. Read results
        dut._log.info("")
        dut._log.info("Step 4: Reading results...")
        
        # Candidate 1
        dut.uio_in.value = 0b00
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        try:
            c1_votes = int(dut.uio_out.value) & 0x7F
            dut._log.info(f"  Candidate 1: {c1_votes} votes")
        except Exception as e:
            dut._log.error(f"  ERROR reading C1: {e}")
            c1_votes = 0
        
        # Candidate 2
        dut.uio_in.value = 0b01
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        try:
            c2_votes = int(dut.uio_out.value) & 0x7F
            dut._log.info(f"  Candidate 2: {c2_votes} votes")
        except Exception as e:
            dut._log.error(f"  ERROR reading C2: {e}")
            c2_votes = 0
        
        # Candidate 3
        dut.uio_in.value = 0b10
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        try:
            c3_votes = int(dut.uio_out.value) & 0x7F
            dut._log.info(f"  Candidate 3: {c3_votes} votes")
        except Exception as e:
            dut._log.error(f"  ERROR reading C3: {e}")
            c3_votes = 0
        
        # Check invalid results flag
        try:
            invalid = (int(dut.uo_out.value) >> 2) & 0x01
            dut._log.info(f"  Tie flag: {invalid}")
        except Exception as e:
            dut._log.error(f"  ERROR reading invalid flag: {e}")
            invalid = 0
        
        # 5. Verify results
        dut._log.info("")
        dut._log.info("="*70)
        dut._log.info(f"EXPECTED: C1=3, C2=3, C3=2")
        dut._log.info(f"ACTUAL:   C1={c1_votes}, C2={c2_votes}, C3={c3_votes}")
        dut._log.info("="*70)
        
        # Soft assertions with detailed messages
        passed = True
        
        if c1_votes != 3:
            dut._log.error(f"✗ FAIL: C1 should be 3, got {c1_votes}")
            passed = False
        else:
            dut._log.info("✓ PASS: C1 = 3")
        
        if c2_votes != 3:
            dut._log.error(f"✗ FAIL: C2 should be 3, got {c2_votes}")
            passed = False
        else:
            dut._log.info("✓ PASS: C2 = 3")
        
        if c3_votes != 2:
            dut._log.error(f"✗ FAIL: C3 should be 2, got {c3_votes}")
            passed = False
        else:
            dut._log.info("✓ PASS: C3 = 2")
        
        if invalid != 1:
            dut._log.warning(f"⚠ WARNING: Tie flag should be 1, got {invalid}")
        else:
            dut._log.info("✓ PASS: Tie detected")
        
        # Final assertion
        if passed:
            dut._log.info("")
            dut._log.info("="*70)
            dut._log.info("✓✓✓ TEST PASSED ✓✓✓")
            dut._log.info("="*70)
        else:
            dut._log.error("")
            dut._log.error("="*70)
            dut._log.error("✗✗✗ TEST FAILED ✗✗✗")
            dut._log.error("="*70)
            assert False, f"Vote counts don't match: C1={c1_votes}, C2={c2_votes}, C3={c3_votes}"
    
    except Exception as e:
        dut._log.error("="*70)
        dut._log.error(f"EXCEPTION OCCURRED: {e}")
        dut._log.error("="*70)
        raise
