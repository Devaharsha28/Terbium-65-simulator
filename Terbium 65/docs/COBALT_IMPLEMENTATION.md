# Cobalt — Balanced-Ternary CPU Implementation

Cobalt is a complete 9-trit CPU built entirely from the simulator's existing
builtin chips, emitted as ordinary project JSON. No simulator code was
modified. The design lives in `Tools/cobalt/` and generates the project
`TestData/Projects/Cobalt/` (mirrored to
`build_win/Terbium 65_Data/Projects/Cobalt/`).

## Architecture

```
COBALT (top)
├── ROM 19683x9            program memory (19683 words, addr = pc + 9841)
├── PH / BOOT MEMs         phase generator (EXEC / WB)
├── PC                    9 x MEM 1TRIT + merge
├── REGFILE               27 x 9-trit regs, 3 address ports, MON outputs
├── RAM27                 27 x 9-trit data memory
└── EXEC
    ├── DECODE            44 opcode lines + IMM_MODE + SHIFT_IMM
    ├── ALU
    │   ├── ADDER9 / SUB9 / CMP9
    │   ├── MIN9/MAX9/MUL9/CONS9/ANY9/IS9
    │   ├── SHIFT9 (4-stage barrel shifter + amount ROM)
    │   ├── 9 x MUX2 (B = reg | imm)
    │   └── 18-candidate tri-state result mux
    └── CTRL
        ├── CMP9 (X vs 0) for register jumps
        ├── jump condition logic (FLAG / CARRY / X-test)
        ├── OFF_FINAL = TAKEN ? (F2? imm5 : RA9) : 1
        └── ADDER9 -> NEXTPC, write enables, addresses
```

Two-phase execution per instruction:

- **EXEC** (`PH == -1`): `EXEC` stage MEMs capture the ALU/CTRL bundle
  (next PC, write data/address/enables, flag/carry data, RAM write, halt).
- **WB** (`PH == +1`): the staged bundle is committed — PC, REGFILE, RAM27,
  FLAG, CARRY, HALT all write from the *stable* stage outputs.

Because the stage registers decouple compute from commit, the CPU is
correct even though the phase timing itself is nondeterministic (see
`COBALT_DECISIONS.md`).

## ISA

81-entry 4-trit opcode space, 44 defined opcodes, 37 reserved -> NOP.
Full definition in `Tools/cobalt/isa.py` (`OPCODE_TABLE`). Operand fields
(leftmost trit = most significant):

- `o3 o2 o1 o0` opcode at trits 8..5
- `A` (2 trits, active reg -4..4) at trits 4..3
- `X` (3 trits, general reg -13..13 or immediate) at trits 2..0
- `imm5` = value of trits 0..4 (used by F2 jumps)

Instruction classes: ALU reg/imm (`ADD SUB MUL MIN MAX CONS ANY IS CMP`),
shifts (`SHL SHR RL RR`, reg or imm amount), `LDI.L/M/H` split loads,
`MOV.AG`/`MOV.GA` between active and general files, `LDA`/`STR` to RAM,
F2 jumps (`JL JE JG JCN JCZ JCP JMP JGE JNE JLE` — flag/carry/imm5 offset),
register jumps (`JN JZ JP` — X reg vs 0, A reg offset), `NOP`, `HALT`.

Assembler: `isa.assemble_program(asm_text)` -> `{addr: instr9}` plus labels.

## Toolchain (`Tools/cobalt/`)

| file | purpose |
|---|---|
| `isa.py` | opcode table, field encode/decode, assembler, `Machine` emulator, `add9/sub9/cmp9/shift9` reference math |
| `test_isa.py` | M1 tests (exhaustive FA, 20k random add/sub, assemble roundtrip, emulator smoke) |
| `validate.py` | project JSON validator + unconnected-input lint |
| `csim.py` | Python replica of the Unity simulator (uint trit encoding, builtin gate tables, dynamic readiness reorder, MEM/PULSE/ROM semantics) |
| `chips.py` | chip-builder DSL: subchips, wires, boundary pins, id allocation, split/merge helpers, JSON emit |
| `blocks.py` | MUX2, ADDER9, SUB9, CMP9, 9-trit TW ops, NOT9, IS9 |
| `blocks2.py` | SHIFT9, DECODE, ALU, CTRL, EXEC, REGFILE, RAM27, COBALT |
| `test_blocks.py` | per-block verification vs csim |
| `gen_cobalt.py` | assemble demo program, build all chips, write project |
| `test_compare.py` / `test_compare2.py` | hardware-vs-emulator per-instruction comparison (manual STEP mode) |
| `test_manual.py` / `dbg_*.py` | stepping driver + debug probes |

## Verification status

- `test_isa.py`: ALL M1 TESTS PASSED
- `test_blocks.py`: ALL BLOCK TESTS PASSED (MUX2 27/27, ADDER9 3026 cases,
  SUB9/CMP9/TW9/IS9/NOT9 verified)
- `test_compare.py`: 10/10 instructions match `isa.Machine`
- `test_compare2.py`: 33/33 instructions match, covering jumps, shifts,
  IS/ANY/CONS/MIN/MAX/MUL, STR/LDA RAM, CMP/flag, HALT
- `validate.py`: clean on Cobalt, Cobalt2, test3, hello

## Regenerating

```
cd Tools/cobalt
python gen_cobalt.py            # demo program -> TestData/Projects/Cobalt
python gen_cobalt2.py           # extended program -> TestData/Projects/Cobalt2
python validate.py "../../TestData/Projects/Cobalt"
```

Copy `TestData/Projects/Cobalt` to
`build_win/Terbium 65_Data/Projects/` for the standalone build.

## Using it in the simulator

- `RESET` +1: clears PC/regs/RAM/flags, PH -> EXEC. Hold >= 2 frames.
- `MODE` +1: auto-run (CLOCK-derived, ~1 instr/s — see decisions doc).
- `MODE` 0/-1: manual — each `STEP` press attempts one phase toggle;
  wait for `PHASE` to change, let the cone settle (~40 frames) between
  EXEC and WB for clean single-stepping.
- Outputs: `PC`, `INSTR`, `FLAG`, `CARRY`, `PHASE`, `HALTED`, `R-4`..`R4`
  (active register monitors).
