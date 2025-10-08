import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
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
async def test_voting_machine(dut):
    dut._log.info("Starting Voting Machine Test")

    # Clock generation (10us -> 100kHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Applying reset")
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # ----------- Test sequence -----------
    dut._log.info("Casting votes...")

    # Vote for candidate 1 (3 times)
    for _ in range(3):
        dut.ui_in.value = 0b001  # candidate_1 high
        await ClockCycles(dut.clk, 1)
        dut.ui_in.value = 0
        await ClockCycles(dut.clk, 1)

    # Vote for candidate 2 (3 times)
    for _ in range(3):
        dut.ui_in.value = 0b010
        await ClockCycles(dut.clk, 1)
        dut.ui_in.value = 0
        await ClockCycles(dut.clk, 1)

    # Vote for candidate 3 (2 times)
    for _ in range(2):
        dut.ui_in.value = 0b100
        await ClockCycles(dut.clk, 1)
        dut.ui_in.value = 0
        await ClockCycles(dut.clk, 1)

    # End of voting
    dut._log.info("Voting over signal")
    dut.ui_in.value = 0b111  # e.g., vote_over
    await ClockCycles(dut.clk, 2)

    # ----------- Check results -----------
    dut._log.info(f"Candidate 1 votes: {dut.uo_out.value & 0xFF}")
    dut._log.info(f"Candidate 2 votes: {(dut.uo_out.value >> 8) & 0xFF}")
    dut._log.info(f"Candidate 3 votes: {(dut.uo_out.value >> 16) & 0xFF}")

    # Assertions (adjust according to your module output mapping)
    assert int(dut.result_1.value) == 3, "Candidate 1 should have 3 votes"
    assert int(dut.result_2.value) == 3, "Candidate 2 should have 3 votes"
    assert int(dut.result_3.value) == 2, "Candidate 3 should have 2 votes"

    dut._log.info("✅ All vote counts are correct!")
