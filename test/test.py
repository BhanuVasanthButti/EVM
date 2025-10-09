import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_voting_machine(dut):
    """Test voting machine through Tiny Tapeout wrapper"""
    
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    dut._log.info("Starting EVM Test")
    
    # Initialize Tiny Tapeout signals
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0  # Active LOW reset in Tiny Tapeout
    
    await ClockCycles(dut.clk, 5)
    
    dut._log.info("De-asserting reset...")
    dut.rst_n.value = 1  # Release reset
    await ClockCycles(dut.clk, 2)
    
    # Start EVM (switch_on_evm)
    dut._log.info("Starting EVM...")
    dut.ui_in.value = 0b00001000  # ui_in[3] = switch_on_evm
    await ClockCycles(dut.clk, 3)
    
    dut._log.info("Casting votes: 3 for C1, 3 for C2, 2 for C3")
    
    # Helper function to cast a vote
    async def cast_vote(candidate_num):
        # Set candidate_ready
        dut.ui_in.value = 0b00011000  # switch_on_evm + candidate_ready
        await ClockCycles(dut.clk, 2)
        
        # Press vote button (clear candidate_ready)
        vote_mask = 1 << (candidate_num - 1)
        dut.ui_in.value = 0b00001000 | vote_mask
        await ClockCycles(dut.clk, 3)
        
        # Release button
        dut.ui_in.value = 0b00001000
        await ClockCycles(dut.clk, 3)
    
    # Cast votes
    for i in range(3):
        await cast_vote(1)  # Candidate 1
    
    for i in range(3):
        await cast_vote(2)  # Candidate 2
    
    for i in range(2):
        await cast_vote(3)  # Candidate 3
    
    dut._log.info("Finished casting votes.")
    
    # End voting session
    dut._log.info("Ending voting session...")
    dut.ui_in.value = 0b00101000  # voting_session_done + switch_on_evm
    await ClockCycles(dut.clk, 5)
    
    # Check results for each candidate
    dut._log.info("Checking results...")
    
    # Display Candidate 1 results
    dut.uio_in.value = 0b00000000  # display_results = 00
    await ClockCycles(dut.clk, 2)
    c1_votes = int(dut.uio_out.value) & 0x7F
    dut._log.info(f"Candidate 1: {c1_votes} votes")
    assert c1_votes == 3, f"C1 should be 3, got {c1_votes}"
    
    # Display Candidate 2 results
    dut.uio_in.value = 0b00000001  # display_results = 01
    await ClockCycles(dut.clk, 2)
    c2_votes = int(dut.uio_out.value) & 0x7F
    dut._log.info(f"Candidate 2: {c2_votes} votes")
    assert c2_votes == 3, f"C2 should be 3, got {c2_votes}"
    
    # Display Candidate 3 results
    dut.uio_in.value = 0b00000010  # display_results = 10
    await ClockCycles(dut.clk, 2)
    c3_votes = int(dut.uio_out.value) & 0x7F
    dut._log.info(f"Candidate 3: {c3_votes} votes")
    assert c3_votes == 2, f"C3 should be 2, got {c3_votes}"
    
    dut._log.info(" All vote counts are correct!")
