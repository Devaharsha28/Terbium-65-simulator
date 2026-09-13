# Terbium 65 — Technical Specifications

This document describes the ternary logic model, signal representation,
components, number systems, and memory architecture implemented by
**Terbium 65**.

Terbium 65 is based on Sebastian Lague's
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim).

---

# 1. Logic System

Terbium uses **balanced ternary logic**.

Each trit has one of three logical values:

| Trit | Meaning |
|---:|---|
| `-1` | Negative |
| `0` | Neutral |
| `+1` | Positive |

A disconnected signal is represented independently from its ternary value.

Therefore:

**Disconnected is not a fourth ternary state.**

---

# 2. Internal Trit Representation

Each trit is represented internally using two logic bits.

| Bits | Trit |
|---|---:|
| `00` | `-1` |
| `01` | `0` |
| `10` | `+1` |

Connection state is stored separately.

For a 9-trit signal:

- 18 bits represent ternary logic values
- 9 bits represent disconnected states
- 27 meaningful state bits are used in total

---

# 3. Signal Widths

Terbium provides three native signal widths:

| Width | Description |
|---:|---|
| 1 trit | Individual ternary signal |
| 3 trits | Small ternary bus |
| 9 trits | Native ternary word |

A 9-trit input/output is displayed using a **3×3 trit grid**.

A 3-trit input/output contains exactly three independently represented trits.

---

# 4. Numerical Interpretation

For a balanced ternary word containing trits:

`t0, t1, t2, ...`

where `t0` is the least-significant trit:

`Value = Σ(t[i] × 3^i)`

For example:

`(+1, 0, -1)`

represents:

`(+1 × 3^0) + (0 × 3^1) + (-1 × 3^2)`

`= 1 - 9`

`= -8`

---

# 5. Numeric Ranges

## 3 Trits

A 3-trit word has:

`3^3 = 27`

possible values.

Range:

`-13 ... +13`

## 9 Trits

A 9-trit word has:

`3^9 = 19,683`

possible values.

Range:

`-9841 ... +9841`

---

# 6. Unary Gates

## BUF

Returns the input unchanged.

| A | OUT |
|---:|---:|
| -1 | -1 |
| 0 | 0 |
| +1 | +1 |

## NOT

Balanced ternary inversion.

| A | OUT |
|---:|---:|
| -1 | +1 |
| 0 | 0 |
| +1 | -1 |

## PNOT

| A | OUT |
|---:|---:|
| -1 | +1 |
| 0 | +1 |
| +1 | -1 |

## NNOT

| A | OUT |
|---:|---:|
| -1 | +1 |
| 0 | -1 |
| +1 | -1 |

## ABS

| A | OUT |
|---:|---:|
| -1 | +1 |
| 0 | 0 |
| +1 | +1 |

## CLU

Clamp Up.

| A | OUT |
|---:|---:|
| -1 | 0 |
| 0 | 0 |
| +1 | +1 |

## CLD

Clamp Down.

| A | OUT |
|---:|---:|
| -1 | -1 |
| 0 | 0 |
| +1 | 0 |

## INC

Cyclic ternary increment.

| A | OUT |
|---:|---:|
| -1 | 0 |
| 0 | +1 |
| +1 | -1 |

## DEC

Cyclic ternary decrement.

| A | OUT |
|---:|---:|
| -1 | +1 |
| 0 | -1 |
| +1 | 0 |

## RTU

Rotate Trit Up.

| A | OUT |
|---:|---:|
| -1 | 0 |
| 0 | +1 |
| +1 | -1 |

RTU currently uses the same logical mapping as INC while remaining a distinct
component.

## RTD

Rotate Trit Down.

| A | OUT |
|---:|---:|
| -1 | +1 |
| 0 | -1 |
| +1 | 0 |

RTD currently uses the same logical mapping as DEC while remaining a distinct
component.

## ISP

Tests whether the input is positive.

| A | OUT |
|---:|---:|
| -1 | -1 |
| 0 | -1 |
| +1 | +1 |

## ISZ

Tests whether the input is zero.

| A | OUT |
|---:|---:|
| -1 | -1 |
| 0 | +1 |
| +1 | -1 |

## ISN

Tests whether the input is negative.

| A | OUT |
|---:|---:|
| -1 | +1 |
| 0 | -1 |
| +1 | -1 |

---

# 7. Binary Gates

Rows represent input **A** and columns represent input **B**.

## AND / MIN

`OUT = min(A, B)`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | -1 | -1 | -1 |
| 0 | -1 | 0 | 0 |
| +1 | -1 | 0 | +1 |

## NAND

`OUT = NOT(MIN(A, B))`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | +1 | +1 | +1 |
| 0 | +1 | 0 | 0 |
| +1 | +1 | 0 | -1 |

## OR / MAX

`OUT = max(A, B)`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | -1 | 0 | +1 |
| 0 | 0 | 0 | +1 |
| +1 | +1 | +1 | +1 |

## NOR

`OUT = NOT(MAX(A, B))`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | +1 | 0 | -1 |
| 0 | 0 | 0 | -1 |
| +1 | -1 | -1 | -1 |

## CONS

Consensus.

If both inputs are equal, their common value is returned.
Otherwise the output is zero.

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | -1 | 0 | 0 |
| 0 | 0 | 0 | 0 |
| +1 | 0 | 0 | +1 |

## NCONS

`OUT = NOT(CONS(A, B))`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | +1 | 0 | 0 |
| 0 | 0 | 0 | 0 |
| +1 | 0 | 0 | -1 |

## ANY

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | -1 | 0 | +1 |
| 0 | 0 | 0 | +1 |
| +1 | +1 | +1 | +1 |

## NANY

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | +1 | 0 | -1 |
| 0 | 0 | 0 | -1 |
| +1 | -1 | -1 | -1 |

## MUL

Arithmetic ternary multiplication.

`OUT = A × B`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | +1 | 0 | -1 |
| 0 | 0 | 0 | 0 |
| +1 | -1 | 0 | +1 |

## NMUL

`OUT = NOT(MUL(A, B))`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | -1 | 0 | +1 |
| 0 | 0 | 0 | 0 |
| +1 | +1 | 0 | -1 |

## SUM

Cyclic single-trit ternary addition.

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | +1 | -1 | 0 |
| 0 | -1 | 0 | +1 |
| +1 | 0 | +1 | -1 |

## NSUM

`OUT = NOT(SUM(A, B))`

| A \ B | -1 | 0 | +1 |
|---:|---:|---:|---:|
| -1 | -1 | +1 | 0 |
| 0 | +1 | 0 | -1 |
| +1 | 0 | -1 | +1 |

---

# 8. Disconnected Signals

Connection state is independent of ternary logic state.

A disconnected signal is therefore different from:

`-1`, `0`, or `+1`.

If a required gate input is disconnected, its output is disconnected.

This prevents floating wires from being interpreted as valid ternary values.

---

# 9. Manual Input

Manual ternary inputs cycle through:

`-1 → 0 → +1 → -1`

Each trit can be changed independently.

---

# 10. Clock

The Clock uses:

| State | Value |
|---|---:|
| LOW | `0` |
| HIGH | `+1` |

Therefore the Clock alternates:

`0 ↔ +1`

---

# 11. Pulse

| State | Value |
|---|---:|
| Idle | `0` |
| Active | `+1` |

---

# 12. Key

| State | Value |
|---|---:|
| Released | `-1` |
| Pressed | `+1` |

---

# 13. Balanced Nonary Representation

Balanced Nonary groups two trits.

For:

`t0, t1`

the group value is:

`groupValue = t0 + 3 × t1`

Possible group values range from:

`-4 ... +4`

Terbium uses:

| Value | Symbol |
|---:|:---:|
| -4 | d |
| -3 | c |
| -2 | b |
| -1 | a |
| 0 | 0 |
| +1 | 1 |
| +2 | 2 |
| +3 | 3 |
| +4 | 4 |

For a 9-trit word, the most-significant unpaired trit is represented
separately.

For example, the minimum 9-trit value:

`---------`

is displayed as:

`adddd`

and represents:

`-9841`

---

# 14. Hept Representation

Terbium's Hept representation groups three balanced ternary trits.

For:

`t0, t1, t2`

the group value is:

`groupValue = t0 + 3 × t1 + 9 × t2`

Possible values range from:

`-13 ... +13`

Negative values use alphabetic symbols:

| Value | Symbol |
|---:|:---:|
| -13 | m |
| -12 | l |
| -11 | k |
| -10 | j |
| -9 | i |
| -8 | h |
| -7 | g |
| -6 | f |
| -5 | e |
| -4 | d |
| -3 | c |
| -2 | b |
| -1 | a |
| 0 | 0 |

Positive values use their decimal values:

`1 ... 13`

Groups are separated by spaces.

For example:

`13 0 m`

represents three grouped values.

---

# 15. Native Ternary ROM

Terbium provides a native:

**19683 × 9-trit ROM**

A 9-trit address provides:

`3^9 = 19,683`

possible addresses.

The balanced address range is:

`-9841 ... +9841`

Internally:

`index = address + 9841`

Therefore:

| Balanced Address | Internal Index |
|---:|---:|
| -9841 | 0 |
| 0 | 9841 |
| +9841 | 19682 |

Each address stores one **9-trit word**.

If the address input is disconnected, the ROM output is disconnected.

ROM locations default to zero and their contents are persisted with the
circuit.

---

# 16. ROM Editor

The native ternary ROM editor supports:

- Ternary
- Decimal
- Nonary
- Hept

Changing the representation does not alter the underlying stored word.

For example, the minimum 9-trit word can be represented as:

| Mode | Representation |
|---|---|
| Ternary | `---------` |
| Decimal | `-9841` |
| Nonary | `adddd` |
| Hept | `m m m` |

All four represent the same underlying ternary value.

---

# 17. Legacy ROM

The original:

**256 × 16 ROM**

from
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim)
is retained separately.

Its original display modes remain:

- Binary
- Decimal
- Hexadecimal

It is separate from Terbium's native ternary ROM.

---

# 18. Known Limitations

## Buzzer

The **Buzzer component is currently non-functional**.

It remains present in the simulator but should not currently be relied upon for
circuit output.

## Legacy Components

Because Terbium originated from
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim),
some binary-oriented components and implementation details remain in the
project.

Not every inherited peripheral has been redesigned specifically for balanced
ternary operation.

---

# 19. Scope

Terbium 65 is intended as an experimental environment for investigating:

- Balanced ternary logic
- Ternary gate systems
- Multi-trit digital circuits
- Ternary buses
- Ternary memory
- Alternative ternary number representations
- Larger experimental ternary architectures

It is not intended to replace commercial EDA or digital logic simulation
software.

---

# 20. References and Acknowledgements

Terbium 65 is based on
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim),
originally created by **Sebastian Lague**.

The following resources were also referenced during the study and
implementation of ternary logic concepts used by the project:

- [Ternary Computing — Louis-Dr](https://louis-dr.github.io/index-ternary.html)
- [Ternary Logic and Arithmetic — Douglas W. Jones](https://homepage.cs.uiowa.edu/~dwjones/ternary/)

These resources are technical references and should not be interpreted as
indicating contribution to or endorsement of Terbium 65.
