# Cobalt ISA Reference

Balanced-ternary CPU. Every instruction = one **9-trit word**
(trits `-1/0/+1`, value range −9841…+9841).

## Instruction word layout

```
trit:  8 7 6 5 | 4 3 | 2 1 0
       opcode |  A  |  X
```

- **opcode** (T8–T5): 4 trits, `(o3,o2,o1,o0)` — see table below
- **A field** (T4,T3): 2 trits → **active register** r-4…r4
- **X field** (T0–T2): 3 trits → **general register** r-13…r13,
  or a small signed immediate (−13…+13) for imm/shift forms

## Registers

- 9 **active** regs `r-4`…`r4` — ALU operands, LDI targets, jump offsets
- 27 **general** regs `r-13`…`r13` — the full register file (X operands,
  LDA addresses, jump-test regs, MOV data)
- `MOV.AG rA, rX`: active[A] ← general[X]
- `MOV.GA rA, rX`: general[X] ← active[A]

## Opcodes (44 of 81 defined; rest = NOP)

`o3` = T8, `o2` = T7, `o1` = T6, `o0` = T5.
`-` = −1, `0` = 0, `+` = +1.

### ALU — o3 = −1

| opcode | reg form | imm form |
|---|---|---|
| `(−,−,−,−)` | `ADD rA, rX` | `ADD rA, imm` |
| `(−,−,0,−)` | `SUB rA, rX` | — |
| `(−,−,+,−)` | `MUL rA, rX` | — |
| `(−,0,−,−)` | `MIN rA, rX` | — |
| `(−,0,0,−)` | `MAX rA, rX` | — |
| `(−,0,+,−)` | `CONS rA, rX` | `CONS rA, imm` |
| `(−,+,−,−)` | `ANY rA, rX` | `ANY rA, imm` |
| `(−,+,0,−)` | `IS rA, rX` | `IS rA, imm` |
| `(−,+,+,−)` | `CMP rA, rX` | `CMP rA, imm` |

`imm` form uses X field as a 3-trit immediate (zero-extended to 9 trits).
`CMP` writes **FLAG** (−1/0/+1), not the register. `ADD`/`SUB` set
**CARRY** on overflow.

### Shifts — o3 = 0, o2 = −1/0

| opcode | reg | imm |
|---|---|---|
| `(0,−,−,−)` | `SHL` | `SHL rA, imm` |
| `(0,−,0,−)` | `SHR` | `SHR rA, imm` |
| `(0,−,+,−)` | `RL` (rotate left) | imm |
| `(0,0,−,−)` | `RR` (rotate right) | imm |

Amount = low 3 trits of X reg (reg form) or the immediate (imm form).

### Data movement — o3 = 0, o2 = 0/+

| opcode | instr |
|---|---|
| `(0,0,0,−)` | `HALT` — stop CPU |
| `(0,0,0,0)` | `NOP` |
| `(0,0,+,−)` | `LDI.L rA, imm3` — load low trits, **zero upper 6** |
| `(0,0,+,0)` | `LDI.M rA, imm3` — patch trits 3–5 |
| `(0,0,+,+)` | `LDI.H rA, imm3` — patch trits 6–8 |
| `(0,+,−,−)` | `MOV.AG rA, rX` |
| `(0,+,−,+)` | `MOV.GA rA, rX` |
| `(0,+,0,−)` | `LDA rA, rX` — rA ← RAM[low3(rX)+13] |
| `(0,+,0,+)` | `STR rA, rX` — RAM[low3(rA)+13] ← rX |

### Jumps — o3 = +1 (relative to *current* PC)

Flag/carry family, offset = imm5 (low 5 trits, −121…+121):

| opcode | condition |
|---|---|
| `(1,−,−,−)` `JL` | FLAG = −1 |
| `(1,−,−,0)` `JE` | FLAG = 0 |
| `(1,−,−,+)` `JG` | FLAG = +1 |
| `(1,−,0,−)` `JCN` | CARRY = −1 |
| `(1,−,0,0)` `JCZ` | CARRY = 0 |
| `(1,−,0,+)` `JCP` | CARRY = +1 |
| `(1,−,+,0)` `JMP` | always |
| `(1,0,−,−)` `JGE` | FLAG ≥ 0 |
| `(1,0,−,0)` `JNE` | FLAG ≠ 0 |
| `(1,0,−,+)` `JLE` | FLAG ≤ 0 |

Register-test family, offset = **full 9-trit value of rA**:

| opcode | condition on rX |
|---|---|
| `(1,+,−,−)` `JN` | rX < 0 |
| `(1,+,−,0)` `JZ` | rX = 0 |
| `(1,+,−,+)` `JP` | rX > 0 |

## Memory map

- **PC** starts at −9841 → ROM row 0; `PC+9841` = ROM row.
- **RAM**: 27 cells, address = low3(reg)+13 (cells 0–26 ↔ −13…+13).
- **Registers**: 27×9 trits; only r-4…r4 are ALU-visible directly.
