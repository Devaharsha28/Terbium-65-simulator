# Cobalt Assembly — Basics & Instruction Tour

Every Cobalt instruction is one **9-trit word**. This file shows small,
verified programs with their ternary encodings for pasting into the
`ROM 19683x9` editor (TERNARY or DECIMAL mode).

## How to load a program

1. Open the **Cobalt** project, place **COBALT_SYS** (or wire your own
   `COBALT` core to a `ROM 19683x9`: `COBALT.PC → ROM.ADDRESS`,
   `ROM.DATA → COBALT.INSTR`).
2. Open the ROM's edit menu — program goes at **rows 0, 1, 2, …**
   (PC starts at −9841, which maps to row 0).
3. TERNARY mode wants 9 chars of `-`/`0`/`+` (**MSB first**).
   DECIMAL mode wants the signed value (−9841…+9841).
4. Run: `RESET=+1` for a couple frames, release, `MODE=0` + tap `STEP`,
   or `MODE=+1` for auto (~1 instr/sec).

## Program 1 — first program (6 instructions)

```asm
        LDI.L r1, 1     ; r1 = 1
        LDI.L r2, 2     ; r2 = 2
        ADD  r1, r2     ; r1 = r1 + r2 = 3
        MOV.GA r1, r5   ; r5 = r1  (general reg, invisible on R-pins)
        MOV.AG r3, r5   ; r3 = r5 = 3  (active reg -> visible as R3)
        HALT
```

| # | asm | ternary | dec |
|---|-----|---------|-----|
| 0 | `LDI.L r1, 1` | `00+-0+00+` | 514 |
| 1 | `LDI.L r2, 2` | `00+-+-0+-` | 542 |
| 2 | `ADD r1, r2` | `----0+0+-` | -9691 |
| 3 | `MOV.GA r1, r5` | `0+-+0++--` | 1733 |
| 4 | `MOV.AG r3, r5` | `0+--+0+--` | 1301 |
| 5 | `HALT` | `000-00000` | -243 |

**Expected:** `R1=3`, `R3=3`, `HALTED=1`, PC frozen.

## Program 2 — loop: sum 1..10 (8 instructions)

```asm
        LDI.L r1, 0     ; sum = 0
        LDI.L r2, 1     ; i = 1
loop:   ADD  r1, r2     ; sum += i
        ADD  r2, 1      ; i++
        CMP  r2, 11     ; flag = cmp(i, 11)
        JL   loop       ; i < 11 -> repeat  (sums 1..10)
        MOV.AG r4, r1   ; r4 = sum -> visible as R4
        HALT
```

| # | asm | ternary | dec |
|---|-----|---------|-----|
| 0 | `LDI.L r1, 0` | `00+-0+000` | 513 |
| 1 | `LDI.L r2, 1` | `00+-+-00+` | 541 |
| 2 | `loop: ADD r1, r2` | `----0+0+-` | -9691 |
| 3 | `ADD r2, 1` | `---0+-00+` | -9422 |
| 4 | `CMP r2, 11` | `-++0+-++-` | -3580 |
| 5 | `JL loop` | `+---000-0` | 3399 |
| 6 | `MOV.AG r4, r1` | `0+--++00+` | 1324 |
| 7 | `HALT` | `000-00000` | -243 |

**Expected:** `R1=55`, `R4=55`, `HALTED=1`.

## Instruction cheat-sheet used above

| instr | meaning |
|---|---|
| `LDI.L rA, v` | rA = v (low 3 trits; **zeroes upper trits**) |
| `LDI.M` / `LDI.H` | patch middle/high trit group, keep rest |
| `ADD/SUB rA, rX` | rA ±= rX (rX = general reg **or** small imm) |
| `CMP rA, rX` | FLAG = compare(rA, rX): −1 / 0 / +1 |
| `MOV.AG rA, rX` | active[A] ← general[X] |
| `MOV.GA rA, rX` | general[X] ← active[A] |
| `Jcc off` / `JMP off` | jump PC += off if flag/carry condition |
| `HALT` / `NOP` | stop / nothing |

See `COBALT_ISA.md` (or ask) for the full 44-opcode table.
