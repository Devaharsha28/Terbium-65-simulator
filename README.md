# Terbium 65

**Terbium 65** is an experimental digital logic simulator designed for
**balanced ternary computing**.

Instead of conventional binary logic, Terbium operates using three logic states:

- `-1` — Negative
- `0` — Neutral
- `+1` — Positive

Terbium 65 is based on Sebastian Lague's
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim),
extended and modified to support ternary logic, ternary gates, multi-trit
signals, ternary memory, and ternary-oriented number representations.

---

## Features

### Balanced Ternary Logic

Terbium uses balanced ternary logic with three states:

`-1`, `0`, `+1`

Disconnected or floating signals are represented independently and are **not**
treated as a fourth logic state.

### Ternary Logic Gates

Terbium includes a collection of unary and binary ternary logic gates.

**Unary gates**

`BUF` `NOT` `PNOT` `NNOT` `ABS` `CLU` `CLD`  
`INC` `DEC` `RTU` `RTD` `ISP` `ISZ` `ISN`

**Binary gates**

`AND/MIN` `NAND` `OR/MAX` `NOR`  
`CONS` `NCONS` `ANY` `NANY`  
`MUL` `NMUL` `SUM` `NSUM`

Exact gate definitions and truth tables are documented in
[SPECIFICATIONS.md](SPECIFICATIONS.md).

### Native Trit Widths

Terbium supports native:

- **1-trit**
- **3-trit**
- **9-trit**

9-trit inputs and outputs use a **3×3 trit layout**.

Bus splitting and merging allow multi-trit circuits to be constructed while
preserving the individual state of each trit.

### Number Representations

Ternary values can be viewed using:

- Balanced Ternary
- Decimal
- Balanced Nonary
- Hept

These provide different textual representations of the same underlying ternary
word.

### Native Ternary ROM

Terbium includes a native:

**19683 × 9-trit ROM**

A 9-trit address provides:

`3^9 = 19,683`

addressable locations.

Balanced addresses range from:

`-9841` to `+9841`

ROM contents can be viewed and edited using Ternary, Decimal, Nonary, and Hept
representations.

The legacy **256 × 16 ROM** inherited from
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim)
is retained separately.

### Input and Control Components

Terbium includes components such as:

- Manual ternary inputs
- Clock
- Pulse
- Key
- Tri-state buffer
- ROM

Manual ternary inputs cycle through:

`-1 → 0 → +1 → -1`

---

## Technical Reference

For exact implementation details, see:

### [Terbium 65 Technical Specifications](SPECIFICATIONS.md)

The specification documents:

- Logic-state representation
- Internal trit encoding
- Gate definitions and truth tables
- Multi-trit signals
- Disconnected signal handling
- Number representations
- Native ROM architecture
- Input and control behavior

---

## Known Limitations

Terbium 65 is an experimental simulator and is not intended to be a
production-grade EDA tool.

Current known limitations include:

- **The Buzzer component is currently non-functional.**
- Some legacy binary-oriented components remain for compatibility.
- Some secondary/peripheral components inherited from Digital Logic Sim have
  not been redesigned specifically for ternary operation.
- Additional bugs may exist in less frequently used components.

---

## Why Terbium?

Most digital logic simulators are designed around binary computation.

Terbium explores what happens when the simulation environment itself is adapted
around **balanced ternary logic**.

It provides a visual environment for experimenting with ternary gates,
multi-trit signals, memory systems, number representations, and larger
experimental ternary architectures.

---

## Development

Terbium 65 is built using **Unity and C#**.

The project focuses on:

- Balanced ternary circuit simulation
- Ternary logic gates
- Multi-trit signals and buses
- Ternary memory
- Alternative ternary number representations
- Experimental ternary digital systems

Terbium has reached a usable experimental state. Development currently
prioritizes stability and bug fixes over major new features.

---

## Credits and References

### Digital Logic Sim

Terbium 65 is based on
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim),
originally created by **Sebastian Lague**.

The original project provides the simulator architecture and foundation upon
which Terbium's ternary functionality was developed.

Terbium 65 is an independent experimental modification and is not affiliated
with Sebastian Lague.

### Ternary Computing References

The following resources were referenced while studying ternary logic,
representations, arithmetic, and ternary computing concepts:

- [Ternary Computing — Louis-Dr](https://louis-dr.github.io/index-ternary.html)
- [Ternary Logic and Arithmetic — Douglas W. Jones](https://homepage.cs.uiowa.edu/~dwjones/ternary/)

These resources are cited as technical references and are not presented as
contributors to Terbium 65.

---

## License

Terbium 65 is derived from the MIT-licensed
[Digital Logic Sim](https://github.com/SebLague/Digital-Logic-Sim).

The original project's copyright and license notices must be retained in
accordance with its license.

See [LICENSE](LICENSE) for licensing information.
