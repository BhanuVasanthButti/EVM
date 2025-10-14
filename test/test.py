# test/test.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

CLK_NS = 20  # 200 MHz


def set_bit(val: int, bit: int, on: bool) -> int:
    return (val | (1 << bit)) if on else (val & ~(1 << bit))


async def tick(dut, n=1):
    for _ in range(n):
        await RisingEdge(dut.clk)


async def reset(dut):
    # Active-low reset on rst_n
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await tick(dut, 5)
    dut.rst_n.value = 1
    await tick(dut, 2)


async def pulse_ui_bit(dut, ui_shadow: int, bit: int, cycles_high=1):
    """Pulse ui_in[bit] high for cycles_high, then low. Returns updated ui_shadow."""
    ui_shadow = set_bit(ui_shadow, bit, True)
    dut.ui_in.value = ui_shadow
    await tick(dut, cycles_high)
    ui_shadow = set_bit(ui_shadow, bit, False)
    dut.ui_in.value = ui_shadow
    await tick(dut, 1)
    return ui_shadow


async def start_machine(dut, ui_shadow: int):
    # switch_on_evm is ui_in[3]; set 1 to turn on
    ui_shadow = set_bit(ui_shadow, 3, True)
    dut.ui_in.value = ui_shadow
    await tick(dut, 1)
    return ui_shadow


async def start_candidate_flow(dut, ui_shadow: int):
    # candidate_ready is ui_in[4]
    # Your FSM needs candidate_ready=1 (→ WAITING_FOR_CANDIDATE_TO_VOTE),
    # then it must be 0 during the actual button press.
    ui_shadow = await pulse_ui_bit(dut, ui_shadow, 4, cycles_high=1)  # goes back to 0
    return ui_shadow


async def press_vote(dut, ui_shadow: int, cand: int):
    """
    cand ∈ {1,2,3}
      vote_candidate_1 = ui_in[0]
      vote_candidate_2 = ui_in[1]
      vote_candidate_3 = ui_in[2]
    Must be pressed while candidate_ready==0 (your RTL checks !candidate_ready).
    """
    # drive exactly one vote bit high for one cycle
    if cand == 1:
        ui_shadow = set_bit(ui_shadow, 0, True)
    elif cand == 2:
        ui_shadow = set_bit(ui_shadow, 1, True)
    elif cand == 3:
        ui_shadow = set_bit(ui_shadow, 2, True)
    else:
        raise ValueError("cand must be 1, 2, or 3")

    dut.ui_in.value = ui_shadow
    await tick(dut, 1)

    # release vote buttons
    ui_shadow = set_bit(ui_shadow, 0, False)
    ui_shadow = set_bit(ui_shadow, 1, False)
    ui_shadow = set_bit(ui_shadow, 2, False)
    dut.ui_in.value = ui_shadow

    # give FSM time to go to CANDIDATE_VOTED and update counters
    await tick(dut, 2)
    return ui_shadow


async def end_voting_session(dut, ui_shadow: int):
    # voting_session_done is ui_in[5]; assert in WAITING_FOR_CANDIDATE
    ui_shadow = await pulse_ui_bit(dut, ui_shadow, 5, cycles_high=1)
    return ui_shadow


async def set_display_results(dut, sel: int):
    # uio_in[1:0] selects which candidate to display when display_winner=0
    dut.uio_in.value = sel & 0b11
    await tick(dut, 1)


async def set_display_winner(dut, on: bool):
    # ui_in[7] controls display_winner
    ui_shadow = int(dut.ui_in.value)
    ui_shadow = set_bit(ui_shadow, 7, on)
    dut.ui_in.value = ui_shadow
    await tick(dut, 1)
    return ui_shadow


def read_candidate_name(dut) -> int:
    # uo_out[1:0]
    return int(dut.uo_out.value) & 0b11


def read_invalid(dut) -> int:
    # uo_out[2]
    return (int(dut.uo_out.value) >> 2) & 0b1


def read_results(dut) -> int:
    # results is on uio_out[6:0]
    return int(dut.uio_out.value) & 0x7F


@cocotb.test()
async def test_normal_voting_and_winner(dut):
    """
    Scenario:
      - Turn on EVM
      - Votes: C1 x3, C2 x2, C3 x1
      - End session
      - Expect: invalid_results=0, Winner = C1 (name=01), winner count=3
      - Per-candidate readback via display_results
    """
    cocotb.start_soon(Clock(dut.clk, CLK_NS, units="ns").start())

    await reset(dut)
    ui = 0

    # sanity: ena may be tied high by TT infra; we don't use it in test

    # Start machine: IDLE -> WAITING_FOR_CANDIDATE
    ui = await start_machine(dut, ui)

    # Cast votes
    for _ in range(3):
        ui = await start_candidate_flow(dut, ui)
        ui = await press_vote(dut, ui, 1)

    for _ in range(2):
        ui = await start_candidate_flow(dut, ui)
        ui = await press_vote(dut, ui, 2)

    ui = await start_candidate_flow(dut, ui)
    ui = await press_vote(dut, ui, 3)

    # End session: WAITING_FOR_CANDIDATE -> VOTING_PROCESS_DONE
    ui = await end_voting_session(dut, ui)

    # Check no tie
    exp_invalid = 0
    act_invalid = read_invalid(dut)
    assert act_invalid == exp_invalid, f"[invalid_results] expected {exp_invalid}, got {act_invalid}"

    # Display winner
    ui = await set_display_winner(dut, True)
    exp_winner_name = 0b01  # C1
    exp_winner_count = 3
    act_winner_name = read_candidate_name(dut)
    act_winner_count = read_results(dut)

    assert act_winner_name == exp_winner_name, (
        f"[winner.name] expected {exp_winner_name:02b}, got {act_winner_name:02b}"
    )
    assert act_winner_count == exp_winner_count, (
        f"[winner.count] expected {exp_winner_count}, got {act_winner_count}"
    )

    # Display individual counts (display_winner=0)
    ui = await set_display_winner(dut, False)

    # C1 via display_results=00
    await set_display_results(dut, 0b00)
    exp_name_c1 = 0b01
    exp_c1 = 3
    act_name_c1 = read_candidate_name(dut)
    act_c1 = read_results(dut)
    assert act_name_c1 == exp_name_c1, f"[C1.name] expected {exp_name_c1:02b}, got {act_name_c1:02b}"
    assert act_c1 == exp_c1, f"[C1.count] expected {exp_c1}, got {act_c1}"

    # C2 via display_results=01
    await set_display_results(dut, 0b01)
    exp_name_c2 = 0b10
    exp_c2 = 2
    act_name_c2 = read_candidate_name(dut)
    act_c2 = read_results(dut)
    assert act_name_c2 == exp_name_c2, f"[C2.name] expected {exp_name_c2:02b}, got {act_name_c2:02b}"
    assert act_c2 == exp_c2, f"[C2.count] expected {exp_c2}, got {act_c2}"

    # C3 via display_results=10
    await set_display_results(dut, 0b10)
    exp_name_c3 = 0b11
    exp_c3 = 1
    act_name_c3 = read_candidate_name(dut)
    act_c3 = read_results(dut)
    assert act_name_c3 == exp_name_c3, f"[C3.name] expected {exp_name_c3:02b}, got {act_name_c3:02b}"
    assert act_c3 == exp_c3, f"[C3.count] expected {exp_c3}, got {act_c3}"


@cocotb.test()
async def test_tie_detection(dut):
    """
    Scenario:
      - Turn on EVM
      - Votes: C1 x2, C2 x2, C3 x0
      - End session
      - Expect: invalid_results=1 (tie)
      - We don't assert winner fields in a tie
    """
    cocotb.start_soon(Clock(dut.clk, CLK_NS, units="ns").start())

    await reset(dut)
    ui = 0

    # Start machine
    ui = await start_machine(dut, ui)

    # C1 x2
    for _ in range(2):
        ui = await start_candidate_flow(dut, ui)
        ui = await press_vote(dut, ui, 1)

    # C2 x2
    for _ in range(2):
        ui = await start_candidate_flow(dut, ui)
        ui = await press_vote(dut, ui, 2)

    # End session
    ui = await end_voting_session(dut, ui)

    # Tie expected
    exp_invalid = 1
    act_invalid = read_invalid(dut)
    assert act_invalid == exp_invalid, f"[invalid_results] expected {exp_invalid} on tie, got {act_invalid}"

    # Optional sanity: toggling display_winner shouldn't matter in tie
    ui = await set_display_winner(dut, True)
    await set_display_results(dut, 0b00)  # no meaning in tie, just ensure interface is stable
    await tick(dut, 1)
    
