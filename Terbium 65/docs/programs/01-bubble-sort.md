# Cobalt Assembly — Bubble Sort (RAM)

Sorts 5 values stored in **RAM cells 0–4** (addresses −13…−9) using
nested loops, `CMP`+`JG` for compare-and-swap, and `LDA`/`STR` for
memory access. Verified in the emulator: `[5,3,1,4,2] → [1,2,3,4,5]`
in 225 steps, then `HALTED=1`.

## Register map

| reg | role |
|---|---|
| `r1` | pass counter p (0–3) — active |
| `r2` | inner index j (address value −13…) — active |
| `r3`,`r4` | scratch — active |
| `r5` | saved RAM[j] during swap — general |
| `r6` | j as LDA address — general |
| `r7` | j+1 as LDA address — general |
| `r8` | RAM[j+1] during swap — general |
| `r9` | inner-loop limit j_end — general |

## Assembly

```asm
        LDI.L r1, 5        ; ---- init RAM[0..4] = 5,3,1,4,2 ----
        MOV.GA r1, r5
        LDI.L r2, -13
        STR r2, r5
        LDI.L r1, 3
        MOV.GA r1, r5
        LDI.L r2, -12
        STR r2, r5
        LDI.L r1, 1
        MOV.GA r1, r5
        LDI.L r2, -11
        STR r2, r5
        LDI.L r1, 4
        MOV.GA r1, r5
        LDI.L r2, -10
        STR r2, r5
        LDI.L r1, 2
        MOV.GA r1, r5
        LDI.L r2, -9
        STR r2, r5

        LDI.L r1, 0        ; p = 0
        LDI.L r3, -10
        MOV.GA r3, r9      ; j_end = -10
outer:  LDI.L r2, -13      ; j = -13
inner:  CMP r2, r9         ; j vs j_end
        JG done_inner      ; j > end -> next pass
        MOV.GA r2, r6      ; r6 = j  (LDA addr)
        MOV.AG r3, r2
        ADD r3, 1
        MOV.GA r3, r7      ; r7 = j+1
        LDA r4, r6         ; r4 = RAM[j]
        LDA r3, r7         ; r3 = RAM[j+1]
        CMP r4, r3
        JG swap            ; RAM[j] > RAM[j+1] -> swap
        JMP next_j
swap:   MOV.GA r4, r5      ; r5 = RAM[j]
        MOV.GA r3, r8      ; r8 = RAM[j+1]
        MOV.AG r4, r6
        STR r4, r8         ; RAM[j] = RAM[j+1]
        MOV.AG r4, r7
        STR r4, r5         ; RAM[j+1] = old RAM[j]
next_j: ADD r2, 1          ; j++
        JMP inner
done_inner:
        MOV.AG r3, r9
        ADD r3, -1
        MOV.GA r3, r9      ; j_end--
        ADD r1, 1          ; p++
        CMP r1, 4
        JL outer           ; p < 4 -> next pass
        HALT
```

## Ternary table (paste rows 0–49)

| # | asm | ternary | dec |
|---|-----|---------|-----|
| 0 | `LDI.L r1, 5` | `00+-0++--` | 518 |
| 1 | `MOV.GA r1, r5` | `0+-+0++--` | 1733 |
| 2 | `LDI.L r2, -13` | `00+-+----` | 527 |
| 3 | `STR r2, r5` | `0+0++-+--` | 2489 |
| 4 | `LDI.L r1, 3` | `00+-0+0+0` | 516 |
| 5 | `MOV.GA r1, r5` | `0+-+0++--` | 1733 |
| 6 | `LDI.L r2, -12` | `00+-+---0` | 528 |
| 7 | `STR r2, r5` | `0+0++-+--` | 2489 |
| 8 | `LDI.L r1, 1` | `00+-0+00+` | 514 |
| 9 | `MOV.GA r1, r5` | `0+-+0++--` | 1733 |
| 10 | `LDI.L r2, -11` | `00+-+---+` | 529 |
| 11 | `STR r2, r5` | `0+0++-+--` | 2489 |
| 12 | `LDI.L r1, 4` | `00+-0+0++` | 517 |
| 13 | `MOV.GA r1, r5` | `0+-+0++--` | 1733 |
| 14 | `LDI.L r2, -10` | `00+-+--0-` | 530 |
| 15 | `STR r2, r5` | `0+0++-+--` | 2489 |
| 16 | `LDI.L r1, 2` | `00+-0+0+-` | 515 |
| 17 | `MOV.GA r1, r5` | `0+-+0++--` | 1733 |
| 18 | `LDI.L r2, -9` | `00+-+--00` | 531 |
| 19 | `STR r2, r5` | `0+0++-+--` | 2489 |
| 20 | `LDI.L r1, 0` | `00+-0+000` | 513 |
| 21 | `LDI.L r3, -10` | `00+-+0-0-` | 557 |
| 22 | `MOV.GA r3, r9` | `0+-++0+00` | 1791 |
| 23 | `outer: LDI.L r2, -13` | `00+-+----` | 527 |
| 24 | `inner: CMP r2, r9` | `-++-+-+00` | -3825 |
| 25 | `JG done_inner` | `+--+0+-00` | 3906 |
| 26 | `MOV.GA r2, r6` | `0+-++-+-0` | 1761 |
| 27 | `MOV.AG r3, r2` | `0+--+00+-` | 1298 |
| 28 | `ADD r3, 1` | `---0+000+` | -9395 |
| 29 | `MOV.GA r3, r7` | `0+-++0+-+` | 1789 |
| 30 | `LDA r4, r6` | `0+0-+++-0` | 2058 |
| 31 | `LDA r3, r7` | `0+0-+0+-+` | 2032 |
| 32 | `CMP r4, r3` | `-++-++0+0` | -3777 |
| 33 | `JG swap` | `+--+000+-` | 3890 |
| 34 | `JMP next_j` | `+-+000+-+` | 5110 |
| 35 | `swap: MOV.GA r4, r5` | `0+-++++--` | 1814 |
| 36 | `MOV.GA r3, r8` | `0+-++0+0-` | 1790 |
| 37 | `MOV.AG r4, r6` | `0+--+++-0` | 1329 |
| 38 | `STR r4, r8` | `0+0++++0-` | 2546 |
| 39 | `MOV.AG r4, r7` | `0+--+++-+` | 1330 |
| 40 | `STR r4, r5` | `0+0++++--` | 2543 |
| 41 | `next_j: ADD r2, 1` | `---0+-00+` | -9422 |
| 42 | `JMP inner` | `+-+00-+00` | 5085 |
| 43 | `MOV.AG r3, r9` | `0+--+0+00` | 1305 |
| 44 | `ADD r3, -1` | `---0+000-` | -9397 |
| 45 | `MOV.GA r3, r9` | `0+-++0+00` | 1791 |
| 46 | `ADD r1, 1` | `---00+00+` | -9449 |
| 47 | `CMP r1, 4` | `-++00+0++` | -3614 |
| 48 | `JL outer` | `+---0-0+-` | 3377 |
| 49 | `HALT` | `000-00000` | -243 |

## Expected result

RAM cells 0–4 hold `1, 2, 3, 4, 5` (ascending). `HALTED=1`.
Check `R1`–`R4` outputs during the run to watch counters/scratch.

## Notes

- `STR rA, rX`: `RAM[low3(rA)+13] ← rX` — **address in the ACTIVE reg**,
  data in a general reg.
- `LDA rA, rX`: `rA ← RAM[low3(rX)+13]` — address in a **general** reg.
- Jump offsets are relative to the *current* instruction; the assembler
  computes them from labels.
- To change the data, edit rows 0–19 only (5× `LDI.L`+`MOV.GA`+`LDI.L`+`STR`).
