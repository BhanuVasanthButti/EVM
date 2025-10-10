# SPDX-FileCopyrightText: © 2024 Your Name
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import pytest

CLK_PERIOD = 10  # ns (Tiny Tapeout standard)
RESET_CYCLES = 2


@cocotb.test()
async def test_evm_full_voting(dut):
    """Full voting sequence test for EVM design"""

    # Setup clock
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, units="ns").start())

    # Apply reset (active low)
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(CLK_PERIOD * RESET_CYCLES, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    cocotb.log.info("Reset deasserted")

    # Helper for setting ui_in bits
    # [0] vote_cand1, [1] vote_cand2, [2] vote_cand3,
    # [3] switch_on_evm, [4] candidate_ready, [5] voting_session_done,
    # [6] switch_off_evm, [7] display_winner
    # uio_in[1:0] => display_results

    async def pulse(signal_idx):
        """Pulse a single control bit for 1 clk cycle"""
        dut.ui_in.value |= (1 << signal_idx)
        await RisingEdge(dut.clk)
        dut.ui_in.value &= ~(1 << signal_idx)
        await RisingEdge(dut.clk)

    # 1. Switch ON EVM
    await pulse(3)
    cocotb.log.info("EVM switched ON")

    # 2. Candidate ready
    await pulse(4)
    cocotb.log.info("Candidate ready")

    # 3. Simulate three voters casting votes
    # Vote pattern: C1, C2, C3, C1, C1 → Candidate 1 wins
    for vote_seq in [0, 1, 2, 0, 0]:
        await pulse(vote_seq)
        cocotb.log.info(f"Vote registered for candidate {vote_seq+1}")

    # 4. Voting session done
    await pulse(5)
    cocotb.log.info("Voting session done")

    # 5. Display results (00 → candidate 1, 01 → candidate 2, 10 → candidate 3)
    for result_sel in [0b00, 0b01, 0b10]:
        dut.uio_in.value = result_sel
        await RisingEdge(dut.clk)
        cocotb.log.info(f"Display results switch = {result_sel:02b}")
        await Timer(2 * CLK_PERIOD, units="ns")

    # 6. Display winner
    dut.ui_in.value |= (1 << 7)  # display_winner = 1
    await RisingEdge(dut.clk)
    await Timer(2 * CLK_PERIOD, units="ns")
    dut.ui_in.value &= ~(1 << 7)

    # 7. Switch off EVM
    await pulse(6)
    cocotb.log.info("EVM switched OFF")

    # ---- Assertions ----
    # Candidate 1 should have max votes, hence uo_out[1:0] = 2'b00 (candidate 1)
    # uo_out[4] (voting_done) expected high after session done
    # invalid_results = 0
    assert dut.uo_out.value.integer is not None, "Output not driven"
    assert dut.uo_out[1:0].value == 0, "Winner is not candidate 1"
    assert dut.uo_out[4].value == 1, "Voting done LED not high"
    assert dut.uo_out[2].value == 0, "Invalid results flag high unexpectedly"

    cocotb.log.info("Full voting sequence passed successfully")
