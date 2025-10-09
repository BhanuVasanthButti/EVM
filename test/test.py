# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

# Constants based on the tt_um_evm wrapper mapping:
# UI_IN (Dedicated Inputs):
UI_C1_VOTE        = 0 # ui_in[0]
UI_C2_VOTE        = 1 # ui_in[1]
UI_C3_VOTE        = 2 # ui_in[2]
UI_SWITCH_ON      = 3 # ui_in[3]
UI_CANDIDATE_READY= 4 # ui_in[4]
UI_VOTING_OVER    = 5 # ui_in[5]
UI_SWITCH_OFF     = 6 # ui_in[6]
UI_DISPLAY_WINNER = 7 # ui_in[7]

# UIO_IN (Bidirectional Inputs used for result selection):
UIO_DISPLAY_0     = 0 # uio_in[0]
UIO_DISPLAY_1     = 1 # uio_in[1]

# UO_OUT (Dedicated Outputs):
UO_CANDIDATE_NAME = slice(0, 2) # uo_out[1:0] (Candidate name 01, 10, 11)
UO_INVALID_RESULTS= 2           # uo_out[2]
UO_VOTING_IN_PROGRESS = 3       # uo_out[3]
UO_VOTING_DONE    = 4           # uo_out[4]

# UIO_OUT (Bidirectional Outputs used for result count):
UIO_RESULTS       = slice(0, 7) # uio_out[6:0] (7-bit results count)

# Expected vote tally: C1=2, C2=4, C3=2 (C2 is winner)
VOTING_SEQUENCE = [1, 2, 2, 3, 2, 3, 1, 2] # Candidate 1, 2, 3 index
EXPECTED_COUNTS = {1: 2, 2: 4, 3: 2}
EXPECTED_WINNER = 2 # Candidate 2 has 4 votes

# Candidate Name Mapping (from your combinational block):
# 2'b01: Candidate 1, 2'b10: Candidate 2, 2'b11: Candidate 3
CANDIDATE_NAME_MAP = {1: 0b01, 2: 0b10, 3: 0b11}


async def pulse_input(dut, pin_index, cycles=1):
    """Helper to pulse a single ui_in pin high for one cycle."""
    dut.ui_in.value |= (1 << pin_index)
    await ClockCycles(dut.clk, cycles)
    dut.ui_in.value &= ~(1 << pin_index)


async def pulse_vote(dut, candidate_index):
    """Simulates one complete vote cycle (Ready -> Vote -> Exit)."""
    dut._log.info(f"--- Vote Cycle for C{candidate_index} ---")
    
    # 1. Enter Ballot (WAITING_FOR_CANDIDATE -> WAITING_FOR_CANDIDATE_TO_VOTE)
    await pulse_input(dut, UI_CANDIDATE_READY)
    await RisingEdge(dut.clk)

    # Check LED: Voting in Progress should be ON
    assert dut.uo_out.value.integer & (1 << UO_VOTING_IN_PROGRESS) != 0

    # 2. Cast Vote (WAITING_FOR_CANDIDATE_TO_VOTE -> CANDIDATE_VOTED)
    vote_pin = {1: UI_C1_VOTE, 2: UI_C2_VOTE, 3: UI_C3_VOTE}[candidate_index]
    await pulse_input(dut, vote_pin)
    await RisingEdge(dut.clk)

    # Check LED: Voting Done should be ON (at least temporarily)
    assert dut.uo_out.value.integer & (1 << UO_VOTING_DONE) != 0

    # 3. Exit Ballot (CANDIDATE_VOTED -> WAITING_FOR_CANDIDATE)
    await pulse_input(dut, UI_CANDIDATE_READY) # Pulse a second time to exit
    await RisingEdge(dut.clk)
    
    # Check LEDs: Both should be OFF after exit
    assert (dut.uo_out.value.integer & (1 << UO_VOTING_IN_PROGRESS)) == 0
    assert (dut.uo_out.value.integer & (1 << UO_VOTING_DONE)) == 0


async def check_count(dut, candidate_index, expected_count):
    """Sets uio_in to select the candidate and verifies the output count."""
    
    # Set display selector using UIO_IN[1:0]
    selector_value = {1: 0b00, 2: 0b01, 3: 0b10}[candidate_index]
    
    # Set display_results
    dut.uio_in.value = selector_value 
    await RisingEdge(dut.clk)
    
    # Read the count from UIO_OUT[6:0]
    actual_count = dut.uio_out.value.integer & 0x7F
    
    dut._log.info(f"Checking C{candidate_index}: Expected {expected_count}, Actual {actual_count}")
    assert actual_count == expected_count, f"C{candidate_index} count mismatch: Expected {expected_count}, got {actual_count}"
    
    # Clear UIO_IN
    dut.uio_in.value = 0


@cocotb.test()
async def test_evm_full_flow(dut):
    dut._log.info("Starting EVM Full Flow Test")

    # Use 10 us period (100 KHz) for stability, standard in TT
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Initial Setup and Reset (Active-Low)
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0 # Apply reset (EVM should be in IDLE)
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1 # De-assert reset
    await ClockCycles(dut.clk, 2)

    # ------------------------------------------------------------------
    # 1. Start Voting (IDLE -> WAITING_FOR_CANDIDATE)
    # ------------------------------------------------------------------
    dut._log.info("1. Starting EVM from IDLE...")
    await pulse_input(dut, UI_SWITCH_ON)
    await ClockCycles(dut.clk, 2) # Settle in WAITING_FOR_CANDIDATE

    # ------------------------------------------------------------------
    # 2. Run Voting Sequence (8 Votes)
    # ------------------------------------------------------------------
    dut._log.info("2. Casting 8 votes...")
    for vote_num, candidate in enumerate(VOTING_SEQUENCE, 1):
        dut._log.info(f"Vote {vote_num}: C{candidate}")
        await pulse_vote(dut, candidate)
        await ClockCycles(dut.clk, 5) # Time between candidates

    # ------------------------------------------------------------------
    # 3. End Voting Session (WAITING -> VOTING_PROCESS_DONE)
    # ------------------------------------------------------------------
    dut._log.info("3. Ending voting session...")
    await pulse_input(dut, UI_VOTING_OVER)
    await ClockCycles(dut.clk, 2)

    # ------------------------------------------------------------------
    # 4. Check Individual Counts
    # ------------------------------------------------------------------
    dut._log.info("4. Checking final tally.")
    # Check C1 (Expected 2)
    await check_count(dut, 1, EXPECTED_COUNTS[1]) 
    # Check C2 (Expected 4)
    await check_count(dut, 2, EXPECTED_COUNTS[2]) 
    # Check C3 (Expected 2)
    await check_count(dut, 3, EXPECTED_COUNTS[3]) 

    # Check for tie condition (invalid_results should be 0)
    assert (dut.uo_out.value.integer >> UO_INVALID_RESULTS) & 1 == 0, "Error: Invalid results (Tie) flag should be low."

    # ------------------------------------------------------------------
    # 5. Check Winner Display
    # ------------------------------------------------------------------
    dut._log.info("5. Checking winner display.")
    
    # Set display_winner bit high (ui_in[7])
    dut.ui_in.value |= (1 << UI_DISPLAY_WINNER)
    await RisingEdge(dut.clk)
    
    # Check Winner Count (should be C2 count = 4)
    winner_count_actual = dut.uio_out.value.integer & 0x7F
    assert winner_count_actual == EXPECTED_COUNTS[EXPECTED_WINNER], \
        f"Winner count mismatch: Expected {EXPECTED_COUNTS[EXPECTED_WINNER]}, got {winner_count_actual}"

    # Check Winner Name (should be C2 name = 2'b10)
    winner_name_actual = dut.uo_out.value.integer & 0x03
    expected_name = CANDIDATE_NAME_MAP[EXPECTED_WINNER]
    assert winner_name_actual == expected_name, \
        f"Winner name mismatch: Expected {expected_name:b}, got {winner_name_actual:b}"

    # Clear display_winner
    dut.ui_in.value &= ~(1 << UI_DISPLAY_WINNER)
    await ClockCycles(dut.clk, 1)

    # ------------------------------------------------------------------
    # 6. Shutdown EVM (VOTING_PROCESS_DONE -> IDLE)
    # ------------------------------------------------------------------
    dut._log.info("6. Shutting down EVM.")
    await pulse_input(dut, UI_SWITCH_OFF)
    await ClockCycles(dut.clk, 10)

    dut._log.info("Test finished successfully.")
