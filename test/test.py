import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge

@cocotb.test()
async def test_voting_machine(dut):
    # The clock period should be short enough for the debounce/hold to work.
    # Your Verilog uses a hold count of 0 to F (16 cycles). 
    # A 10us clock (100kHz) is acceptable.
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    dut._log.info("Starting EVM Test")

    # Initialize ALL inputs (Crucial for Verilog without Tiny Tapeout wrapper)
    dut.i_candidate_1.value = 0
    dut.i_candidate_2.value = 0
    dut.i_candidate_3.value = 0
    dut.i_voting_over.value = 0
    # Your module uses 'rst', not 'rst_n'
    dut.rst.value = 1 
    await ClockCycles(dut.clk, 5)
    
    dut._log.info("De-asserting reset and starting VOTE state...")
    dut.rst.value = 0 # De-assert reset (Active HIGH)
    await ClockCycles(dut.clk, 2) # Wait for FSM to transition from IDLE to VOTE

    # ----------- Test sequence -----------
    # The Verilog counts on the FALLING EDGE (when the button is released).

    dut._log.info("Casting votes: 3 for C1, 3 for C2, 2 for C3")

    # Vote for candidate 1 (3 times)
    for i in range(3):
        dut.i_candidate_1.value = 1  # Press button
        await ClockCycles(dut.clk, 1)
        dut.i_candidate_1.value = 0  # Release button (Vote is counted here)
        await ClockCycles(dut.clk, 1) 
        # Wait for HOLD state to expire (Your debounce is 16 cycles, but 
        # the test sequence provides enough time because we wait for 2 cycles
        # per vote, transitioning to HOLD and then back to VOTE).
        
    # Vote for candidate 2 (3 times)
    for i in range(3):
        dut.i_candidate_2.value = 1
        await ClockCycles(dut.clk, 1)
        dut.i_candidate_2.value = 0 # Vote is counted here
        await ClockCycles(dut.clk, 1)
        
    # Vote for candidate 3 (2 times)
    for i in range(2):
        dut.i_candidate_3.value = 1
        await ClockCycles(dut.clk, 1)
        dut.i_candidate_3.value = 0 # Vote is counted here
        await ClockCycles(dut.clk, 1)

    dut._log.info("Finished casting votes.")

    # End of voting - Finalize the results
    dut._log.info("Asserting i_voting_over...")
    dut.i_voting_over.value = 1 # Assert the voting over signal
    await ClockCycles(dut.clk, 5) # Give time for the outputs to update (FINISH state)

    # ----------- Check results -----------
    
    # Check the state
    assert int(dut.o_count1.value) == 3, f"C1 should be 3, got {int(dut.o_count1.value)}"
    assert int(dut.o_count2.value) == 3, f"C2 should be 3, got {int(dut.o_count2.value)}"
    assert int(dut.o_count3.value) == 2, f"C3 should be 2, got {int(dut.o_count3.value)}"

    dut._log.info("✅ All vote counts are correct!")

    # Optional: De-assert voting_over to transition back to IDLE
    dut._log.info("De-asserting i_voting_over to reset FSM state.")
    dut.i_voting_over.value = 0
    await ClockCycles(dut.clk, 2)
    
    # Check if counters are cleared when returning to IDLE (only when rst is active)
    # The Verilog keeps the outputs displayed until rst is asserted.
    # To check the internal counters are cleared, you'd need a way to monitor r_counter_X.
