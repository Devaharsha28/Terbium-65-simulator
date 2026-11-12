# Cobalt — Design Decisions & Race Analysis

## Why MEM 1TRIT everywhere

Every sequential element is `MEM 1TRIT` (DATA/WE/DATA-out). The builtin's
WE semantics are:

- `WE = +1`: write `DATA` trit
- `WE = 0`: hold
- `WE = -1`: *clear cell to raw 0* (= trit -1, **not** trit 0)

That last point is a trap: raw storage 0 encodes trit -1, 1 encodes 0,
2 encodes +1. Reset therefore writes **logical 0 by muxing const-0 into
DATA and pulsing WE=+1** — never WE=-1.

## The phase machine (EXEC / WB)

A single `PH` MEM holds the phase. `EXEC_EN = CLU(ISN(PH))` and
`WB_pos = CLU(ISP(PH))` are 0/+1-only enables (never -1, which would
clear stage cells instead of holding them).

Why two phases at all: writeback must be atomic. During EXEC the ALU/CTRL
cone (~4 600 chips deep) settles; the EXEC chip's stage MEMs latch the
result; during WB the *stable* stage outputs drive every storage element.
This makes commit insensitive to transient garbage in the compute cone.

### The PH=0 absorbing state

`PH` is binary (±1). A naive `PH.D = NOT(PH)` through a MEM can latch
raw 0 (trit 0), which `NOT(0)=0` keeps forever — an absorbing state that
froze the CPU at startup. Fix: the toggle is
`MAX(NOT(PH), ISZ(NOT(PH)))`, which maps 0 -> +1 (self-corrects) and
swaps -1 <-> +1 normally.

### Toggle timing & the ~50% race

`PH.WE` is a *narrow pulse*, not a level:

- Auto mode: `PULSE(CLOCK, 1)` — one 1-frame pulse per 500-frame clock
  half-period, so each phase holds ~500 frames.
- Manual mode: `PULSE(STEP, 1)` — one pulse per button press.

The pulse makes `PH` a real toggle flip-flop-ish element: it can only
change on a pulse edge. Because `MEM` samples its inputs mid-frame in
simulator order, a pulse that arrives "too late" in the frame is missed —
so a manual STEP press succeeds only ~50% of the time. `wait_phase()` in
the tests presses until `PHASE` actually changes. This is inherent to
unordered gate evaluation, not a bug; it just means manual stepping needs
the user (or test) to confirm the phase moved.

The long phase hold is what makes WB writes atomic: with ~500 frames per
phase, every storage MEM sees a stable WE=+1 and stable DATA for many
consecutive frames — any mid-write hazard window is long past.

## The reset skew bug (and the general fix)

First version: PC MEM `DATA = mux2(S_NEXTPC, 0, rst_isp)` but
`WE = MAX(wb_pos, rst_bit)` where `rst_bit = CLU(rst_isp)`. `rst_isp`
(depth 1) updates a cascade earlier than `rst_bit` (depth 2). On RESET
release, DATA switched to `S_NEXTPC` while WE was still the stale +1 —
PC latched NEXTPC during EXEC. Observed: PC=1 before the first step.

**General rule**: for any MEM whose DATA and WE both depend on a control
signal, both must derive from the *same* qualified signal so they change
in the same propagation cascade. The MEM's readiness requires *both*
inputs to arrive that frame, so it can never see a mixed pair.

Fix: `RQ = CLU(ISP(RESET))` (0/+1) is used as *both* the data-mux select
and the WE reset-term for PC, FLAG, CARRY, HALT, PH, REGFILE and RAM27.

## Stage vs direct writeback

REGFILE/RAM write directly from EXEC outputs during WB (WE = WB_pos &
decode). PC/FLAG/CARRY/HALT write from EXEC *stage* outputs — actually
the same thing, since EXEC stage outputs are the only WB-visible bundle.
The stage exists so EXEC's outputs are stable registers, not the
still-settling comb cone: WB reads `S_*` pins which are MEM-held.

## Reset polarity detail

`RESET = +1` resets; `0`/`-1` run. During reset `PH -> -1` (EXEC) and
every storage element is written 0 via the `rq` path. Hold RESET >= 2
frames so the multi-frame MEM writes all land.

## Known limitations

- **Manual mode is slow & probabilistic**: ~50% toggle success per press,
  ~40-frame settle between phases. Fine for debugging, not for bulk runs.
- **Auto mode ~1 instr/sec**: 500-frame phases × 2 phases = 1000 frames
  per instruction; the ~4 600-chip cone needs the long hold for atomic WB.
  Could be sped up by shortening phases once ordering is verified stable,
  at the cost of re-introducing skew risk.
- **No interrupts, no I/O, no flags beyond CMP carry**. ISA has reserved
  opcode space for extensions.
- **RAM27 uses general regs as address** (low 3 trits of A/X reg, +13
  offset) — matches the ISA's `LDA`/`STR` semantics.
- csim is a *replica*, not the Unity engine — gate tables and reorder were
  mirrored from `Simulator.cs`/`PinState.cs`; behaviour matches on all
  tested programs but Unity's exact frame ordering may differ subtly.

## Files

See `COBALT_IMPLEMENTATION.md` for the module map and
`Tools/cobalt/` for the generator sources.
