
#-------------------EXISISTING CODE ENDS-------------

# Pin mapping based on your tt_um_evm top module
# ui_in[7:0] mapping:
#   ui_in[0] = vote_candidate_1
#   ui_in[1] = vote_candidate_2
#   ui_in[2] = vote_candidate_3
#   ui_in[3] = switch_on_evm
#   ui_in[4] = candidate_ready
#   ui_in[5] = voting_session_done
#   ui_in[6] = switch_off_evm
#   ui_in[7] = display_winner
#
# uio_in[1:0] = display_results
#
# uo_out[7:0] mapping:
#   uo_out[1:0] = candidate_name
#   uo_out[2] = invalid_results
#   uo_out[3] = voting_in_progress
#   uo_out[4] = voting_done
#   uo_out[7:5] = unused (0)
#
# uio_out[6:0] = results (vote count)

@cocotb.test()
async def test_evm_reset(dut):
    """Test: Power-on reset and initialization"""
    dut._log.info("="*60)
    dut._log.info("TEST 1: Reset and Initialization")
    dut._log.info("="*60)
    
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Apply reset
    dut._log.info("Applying reset...")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Check initial state (should be IDLE = 000)
    dut._log.info(f"After reset - uo_out: {dut.uo_out.value}, uio_out: {dut.uio_out.value}")
    assert dut.uo_out.value & 0x03 == 0, "candidate_name should be 0"
    assert (dut.uo_out.value >> 2) & 0x01 == 0, "invalid_results should be 0"
    assert (dut.uo_out.value >> 3) & 0x01 == 0, "voting_in_progress should be 0"
    assert (dut.uo_out.value >> 4) & 0x01 == 0, "voting_done should be 0"
    
    dut._log.info("✓ Reset test passed")


@cocotb.test()
async def test_evm_state_transitions(dut):
    """Test: FSM state transitions (IDLE → WAITING_FOR_CANDIDATE → WAITING_FOR_CANDIDATE_TO_VOTE)"""
    dut._log.info("="*60)
    dut._log.info("TEST 2: State Transitions")
    dut._log.info("="*60)
    
    # Setup clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Test IDLE → WAITING_FOR_CANDIDATE
    dut._log.info("Setting switch_on_evm (ui_in[3])...")
    dut.ui_in.value = 0b00001000  # switch_on_evm = 1
    await ClockCycles(dut.clk, 3)
    dut._log.info(f"After switch_on_evm - uo_out: {dut.uo_out.value}")
    
    # Test WAITING_FOR_CANDIDATE → WAITING_FOR_CANDIDATE_TO_VOTE
    dut._log.info("Setting candidate_ready (ui_in[4])...")
    dut.ui_in.value = 0b00011000  # switch_on_evm=1, candidate_ready=1
    await ClockCycles(dut.clk, 3)
    
    voting_in_progress = (dut.uo_out.value >> 3) & 0x01
    dut._log.info(f"voting_in_progress: {voting_in_progress}")
    assert voting_in_progress == 1, "voting_in_progress should be 1 in WAITING_FOR_CANDIDATE_TO_VOTE"
    
    dut._log.info("✓ State transition test passed")


@cocotb.test()
async def test_evm_single_vote(dut):
    """Test: Single vote for candidate 1"""
    dut._log.info("="*60)
    dut._log.info("TEST 3: Single Vote for Candidate 1")
    dut._log.info("="*60)
    
    # Setup clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Navigate to voting state
    dut._log.info("Transitioning to voting state...")
    dut.ui_in.value = 0b00001000  # switch_on_evm
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0b00011000  # candidate_ready
    await ClockCycles(dut.clk, 2)
    
    # Clear candidate_ready and press vote_candidate_1
    dut._log.info("Voting for candidate 1...")
    dut.ui_in.value = 0b00001001  # vote_candidate_1=1, switch_on_evm=1
    await ClockCycles(dut.clk, 3)
    
    # Release vote button
    dut.ui_in.value = 0b00001000  # Release vote button
    await ClockCycles(dut.clk, 3)
    
    voting_done = (dut.uo_out.value >> 4) & 0x01
    dut._log.info(f"voting_done: {voting_done}")
    assert voting_done == 1, "voting_done should be 1 after vote"
    
    dut._log.info("✓ Single vote test passed")


@cocotb.test()
async def test_evm_multiple_votes(dut):
    """Test: Multiple votes for different candidates"""
    dut._log.info("="*60)
    dut._log.info("TEST 4: Multiple Votes - All Candidates")
    dut._log.info("="*60)
    
    # Setup clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Start EVM
    dut.ui_in.value = 0b00001000  # switch_on_evm
    await ClockCycles(dut.clk, 2)
    
    # Vote 1: Candidate 1
    dut._log.info("Vote 1: Candidate 1")
    dut.ui_in.value = 0b00011000  # candidate_ready
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0b00001001  # vote_candidate_1
    await ClockCycles(dut.clk, 3)
    dut.ui_in.value = 0b00001000  # release
    await ClockCycles(dut.clk, 3)
    
    # Vote 2: Candidate 2
    dut._log.info("Vote 2: Candidate 2")
    dut.ui_in.value = 0b00011000  # candidate_ready
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0b00001010  # vote_candidate_2
    await ClockCycles(dut.clk, 3)
    dut.ui_in.value = 0b00001000  # release
    await ClockCycles(dut.clk, 3)
    
    # Vote 3: Candidate 3
    dut._log.info("Vote 3: Candidate 3")
    dut.ui_in.value = 0b00011000  # candidate_ready
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0b00001100  # vote_candidate_3
    await ClockCycles(dut.clk, 3)
    dut.ui_in.value = 0b00001000  # release
    await ClockCycles(dut.clk, 3)
    
    # Vote 4: Candidate 1 again
    dut._log.info("Vote 4: Candidate 1 again")
    dut.ui_in.value = 0b00011000  # candidate_ready
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0b00001001  # vote_candidate_1
    await ClockCycles(dut.clk, 3)
    dut.ui_in.value = 0b00001000  # release
    await ClockCycles(dut.clk, 3)
    
    dut._log.info("✓ Multiple votes test passed")


@cocotb.test()
async def test_evm_result_display(dut):
    """Test: Vote counting and result display"""
    dut._log.info("="*60)
    dut._log.info("TEST 5: Result Display and Vote Counting")
    dut._log.info("="*60)
    
    # Setup clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Start EVM
    dut.ui_in.value = 0b00001000  # switch_on_evm
    await ClockCycles(dut.clk, 2)
    
    # Cast 3 votes for candidate 1
    for i in range(3):
        dut._log.info(f"Casting vote {i+1} for Candidate 1")
        dut.ui_in.value = 0b00011000  # candidate_ready
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = 0b00001001  # vote_candidate_1
        await ClockCycles(dut.clk, 3)
        dut.ui_in.value = 0b00001000  # release
        await ClockCycles(dut.clk, 3)
    
    # Cast 2 votes for candidate 2
    for i in range(2):
        dut._log.info(f"Casting vote {i+1} for Candidate 2")
        dut.ui_in.value = 0b00011000  # candidate_ready
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = 0b00001010  # vote_candidate_2
        await ClockCycles(dut.clk, 3)
        dut.ui_in.value = 0b00001000  # release
        await ClockCycles(dut.clk, 3)
    
    # End voting session
    dut._log.info("Ending voting session...")
    dut.ui_in.value = 0b00101000  # voting_session_done
    await ClockCycles(dut.clk, 3)
    
    # Display candidate 1 results (display_results = 00)
    dut._log.info("Displaying Candidate 1 results...")
    dut.uio_in.value = 0b00000000  # display_results[1:0] = 00
    await ClockCycles(dut.clk, 2)
    candidate_1_votes = dut.uio_out.value & 0x7F
    candidate_name = dut.uo_out.value & 0x03
    dut._log.info(f"Candidate 1 votes: {candidate_1_votes}, candidate_name: {candidate_name}")
    assert candidate_1_votes == 3, f"Candidate 1 should have 3 votes, got {candidate_1_votes}"
    
    # Display candidate 2 results (display_results = 01)
    dut._log.info("Displaying Candidate 2 results...")
    dut.uio_in.value = 0b00000001  # display_results[1:0] = 01
    await ClockCycles(dut.clk, 2)
    candidate_2_votes = dut.uio_out.value & 0x7F
    candidate_name = dut.uo_out.value & 0x03
    dut._log.info(f"Candidate 2 votes: {candidate_2_votes}, candidate_name: {candidate_name}")
    assert candidate_2_votes == 2, f"Candidate 2 should have 2 votes, got {candidate_2_votes}"
    
    dut._log.info("✓ Result display test passed")


@cocotb.test()
async def test_evm_winner_display(dut):
    """Test: Winner determination and display"""
    dut._log.info("="*60)
    dut._log.info("TEST 6: Winner Determination")
    dut._log.info("="*60)
    
    # Setup clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Start EVM
    dut.ui_in.value = 0b00001000  # switch_on_evm
    await ClockCycles(dut.clk, 2)
    
    # Cast votes: Candidate 1 = 3, Candidate 2 = 2, Candidate 3 = 1
    vote_sequence = [
        (1, 3),  # Candidate 1: 3 votes
        (2, 2),  # Candidate 2: 2 votes
        (3, 1),  # Candidate 3: 1 vote
    ]
    
    for candidate, count in vote_sequence:
        for i in range(count):
            dut._log.info(f"Vote for Candidate {candidate}")
            dut.ui_in.value = 0b00011000  # candidate_ready
            await ClockCycles(dut.clk, 2)
            dut.ui_in.value = 0b00001000 | (1 << (candidate - 1))  # vote button
            await ClockCycles(dut.clk, 3)
            dut.ui_in.value = 0b00001000  # release
            await ClockCycles(dut.clk, 3)
    
    # End voting and display winner
    dut._log.info("Ending voting and displaying winner...")
    dut.ui_in.value = 0b10101000  # voting_session_done + display_winner
    await ClockCycles(dut.clk, 3)
    
    winner = dut.uo_out.value & 0x03
    winner_votes = dut.uio_out.value & 0x7F
    dut._log.info(f"Winner: Candidate {winner}, Votes: {winner_votes}")
    assert winner == 1, f"Winner should be candidate 1, got {winner}"
    assert winner_votes == 3, f"Winner should have 3 votes, got {winner_votes}"
    
    dut._log.info("✓ Winner determination test passed")


@cocotb.test()
async def test_evm_tie_detection(dut):
    """Test: Tie detection when candidates have equal votes"""
    dut._log.info("="*60)
    dut._log.info("TEST 7: Tie Detection")
    dut._log.info("="*60)
    
    # Setup clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    # Start EVM
    dut.ui_in.value = 0b00001000  # switch_on_evm
    await ClockCycles(dut.clk, 2)
    
    # Cast equal votes: Candidate 1 = 2, Candidate 2 = 2
    for _ in range(2):
        # Vote for Candidate 1
        dut.ui_in.value = 0b00011000  # candidate_ready
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = 0b00001001  # vote_candidate_1
        await ClockCycles(dut.clk, 3)
        dut.ui_in.value = 0b00001000  # release
        await ClockCycles(dut.clk, 3)
        
        # Vote for Candidate 2
        dut.ui_in.value = 0b00011000  # candidate_ready
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = 0b00001010  # vote_candidate_2
        await ClockCycles(dut.clk, 3)
        dut.ui_in.value = 0b00001000  # release
        await ClockCycles(dut.clk, 3)
    
    # End voting
    dut._log.info("Checking for tie...")
    dut.ui_in.value = 0b10101000  # voting_session_done + display_winner
    await ClockCycles(dut.clk, 3)
    
    invalid_results = (dut.uo_out.value >> 2) & 0x01
    dut._log.info(f"invalid_results: {invalid_results}")
    assert invalid_results == 1, "invalid_results should be 1 for tie"
    
    dut._log.info("✓ Tie detection test passed")


@cocotb.test()
async def test_evm_full_cycle(dut):
    """Test: Complete EVM cycle from power-on to results"""
    dut._log.info("="*60)
    dut._log.info("TEST 8: Complete EVM Cycle")
    dut._log.info("="*60)
    
    # Setup clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    
    # 1. Turn on EVM
    dut._log.info("1. Turning on EVM...")
    dut.ui_in.value = 0b00001000  # switch_on_evm
    await ClockCycles(dut.clk, 3)
    
    # 2. Simulate complete voting session
    dut._log.info("2. Conducting voting session...")
    votes = [(1, 3), (2, 3), (3, 2)]  # Candidate votes
    
    for candidate, count in votes:
        for vote_num in range(count):
            dut._log.info(f"   Vote {vote_num+1} for Candidate {candidate}")
            dut.ui_in.value = 0b00011000  # candidate_ready
            await ClockCycles(dut.clk, 2)
            dut.ui_in.value = 0b00001000 | (1 << (candidate - 1))
            await ClockCycles(dut.clk, 3)
            dut.ui_in.value = 0b00001000
            await ClockCycles(dut.clk, 3)
    
    # 3. End voting session
    dut._log.info("3. Ending voting session...")
    dut.ui_in.value = 0b00101000  # voting_session_done
    await ClockCycles(dut.clk, 5)
    
    # 4. Display all results
    dut._log.info("4. Displaying results...")
    for i in range(3):
        dut.uio_in.value = i
        await ClockCycles(dut.clk, 2)
        votes_count = dut.uio_out.value & 0x7F
        dut._log.info(f"   Candidate {i+1}: {votes_count} votes")
    
    # 5. Display winner
    dut._log.info("5. Displaying winner...")
    dut.ui_in.value = 0b10101000  # display_winner
    await ClockCycles(dut.clk, 3)
    winner = dut.uo_out.value & 0x03
    dut._log.info(f"   Winner: Candidate {winner}")
    
    # 6. Turn off EVM
    dut._log.info("6. Turning off EVM...")
    dut.ui_in.value = 0b01101000  # switch_off_evm
    await ClockCycles(dut.clk, 5)
    
    dut._log.info("✓ Complete cycle test passed")
    dut._log.info("="*60)
    dut._log.info("ALL TESTS COMPLETED SUCCESSFULLY!")
    dut._log.info("="*60)
