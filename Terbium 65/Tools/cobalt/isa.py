"""Cobalt ISA: trit helpers, opcode table, assembler, emulator.

Instruction = 9 trits, list index 0 = LSB (T0) .. index 8 = MSB (T8).
Opcode = trits [8,7,6,5] = (o3,o2,o1,o0), o3 = T8.

F1 = [op T8..T5][A = T4,T3][X = T2,T1,T0]
F2 = [op T8..T5][imm5 = T4..T0]

Field convention: within a field the LEFTMOST trit is most significant:
  A   = 3*T4 + 1*T3          (2-trit, -4..4,  active register)
  X   = 9*T2 + 3*T1 + 1*T0   (3-trit, -13..13, general register or imm3)
  imm5= 81*T4 + ... + 1*T0   (5-trit, -121..121)

Trits are ints in {-1,0,+1}.
"""

NEG, ZERO, POS = -1, 0, 1
TRITS = (NEG, ZERO, POS)


def trits_value(trits_lsb_first):
    """Balanced ternary value; input list index 0 = weight 1."""
    v, w = 0, 1
    for t in trits_lsb_first:
        v += t * w
        w *= 3
    return v


def value_trits(v, n):
    """Encode integer v as n balanced trits, returns LSB-first list."""
    lo, hi = -((3 ** n - 1) // 2), (3 ** n - 1) // 2
    if not (lo <= v <= hi):
        raise ValueError(f"value {v} out of range for {n} trits [{lo},{hi}]")
    out = []
    rem = v
    for _ in range(n):
        # balanced residue: rem mod 3 in {0,1,2} -> digit {0,+1,-1}
        r = rem % 3
        d = 0 if r == 0 else (1 if r == 1 else -1)
        out.append(d)
        rem = (rem - d) // 3
    return out


# ---------------------------------------------------------------------------
# Opcode table: (o3,o2,o1,o0) -> (mnemonic, kind)
# kind: reg | imm | shift_reg | shift_imm | nop | halt | ldi_l/m/h |
#       mov_ag | mov_ga | lda | str | jump_f2 | jump_reg
# ---------------------------------------------------------------------------
OPCODE_TABLE = {}


def _put(o3, o2, o1, o0, name, kind):
    key = (o3, o2, o1, o0)
    assert key not in OPCODE_TABLE, f"opcode collision at {key}"
    OPCODE_TABLE[key] = (name, kind)


# class o3 = -1 : ALU, F1, o0 = operand mode (-1 reg, 0 imm, +1 reserved)
for o2, o1, mn in ((NEG, NEG, "ADD"), (NEG, POS, "MUL"), (ZERO, NEG, "MIN"),
                   (ZERO, ZERO, "MAX"), (ZERO, POS, "CONS"), (POS, NEG, "ANY"),
                   (POS, ZERO, "IS"), (POS, POS, "CMP")):
    _put(NEG, o2, o1, NEG, mn, "reg")
for o2, o1, mn in ((NEG, NEG, "ADD"), (ZERO, POS, "CONS"), (POS, NEG, "ANY"),
                   (POS, ZERO, "IS"), (POS, POS, "CMP")):
    _put(NEG, o2, o1, ZERO, mn, "imm")
_put(NEG, NEG, ZERO, NEG, "SUB", "reg")

# class o3 = 0
for o2, o1, mn in ((NEG, NEG, "SHL"), (NEG, ZERO, "SHR"), (NEG, POS, "RL"),
                   (ZERO, NEG, "RR")):
    _put(ZERO, o2, o1, NEG, mn, "shift_reg")
    _put(ZERO, o2, o1, ZERO, mn, "shift_imm")
_put(ZERO, ZERO, ZERO, ZERO, "NOP", "nop")
_put(ZERO, ZERO, ZERO, NEG, "HALT", "halt")
_put(ZERO, ZERO, POS, NEG, "LDI.L", "ldi_l")
_put(ZERO, ZERO, POS, ZERO, "LDI.M", "ldi_m")
_put(ZERO, ZERO, POS, POS, "LDI.H", "ldi_h")
_put(ZERO, POS, NEG, NEG, "MOV.AG", "mov_ag")
_put(ZERO, POS, NEG, POS, "MOV.GA", "mov_ga")
_put(ZERO, POS, ZERO, NEG, "LDA", "lda")
_put(ZERO, POS, ZERO, POS, "STR", "str")

# class o3 = +1 : F2 jumps
for o2, o1, o0, mn in (
        (NEG, NEG, NEG, "JL"), (NEG, NEG, ZERO, "JE"), (NEG, NEG, POS, "JG"),
        (NEG, ZERO, NEG, "JCN"), (NEG, ZERO, ZERO, "JCZ"), (NEG, ZERO, POS, "JCP"),
        (NEG, POS, ZERO, "JMP"),
        (ZERO, NEG, NEG, "JGE"), (ZERO, NEG, ZERO, "JNE"), (ZERO, NEG, POS, "JLE")):
    _put(POS, o2, o1, o0, mn, "jump_f2")
# F1 register-test jumps
_put(POS, POS, NEG, NEG, "JN", "jump_reg")
_put(POS, POS, NEG, ZERO, "JZ", "jump_reg")
_put(POS, POS, NEG, POS, "JP", "jump_reg")

MNEMONICS = {}
for opc, (mn, kind) in OPCODE_TABLE.items():
    MNEMONICS.setdefault(mn, []).append((opc, kind))


def check_opcode_table():
    total = 3 ** 4
    print(f"opcode space: {total}, defined: {len(OPCODE_TABLE)}, "
          f"reserved(->NOP): {total - len(OPCODE_TABLE)}")
    # sanity: no duplicate mnemonics with same kind
    for mn, lst in MNEMONICS.items():
        kinds = [k for _, k in lst]
        assert len(kinds) == len(set(kinds)), f"{mn} duplicate kind"


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------

class AsmError(Exception):
    pass


def _parse_reg(tok):
    tok = tok.strip()
    if len(tok) < 2 or tok[0].lower() != "r":
        raise AsmError(f"expected register, got {tok!r}")
    try:
        v = int(tok[1:])
    except ValueError:
        raise AsmError(f"bad register {tok!r}")
    if not -13 <= v <= 13:
        raise AsmError(f"register {tok} out of range -13..13")
    return v


def _parse_imm(tok):
    tok = tok.strip()
    try:
        return int(tok, 0)
    except ValueError:
        raise AsmError(f"bad immediate {tok!r}")


def _opcode_for(mn, kind):
    for opc, (m2, k2) in OPCODE_TABLE.items():
        if m2 == mn and k2 == kind:
            return opc
    raise AsmError(f"no opcode for {mn} as {kind}")


def _emit_f1(opc, a_val, x_val):
    """opc=(o3,o2,o1,o0); a_val 2-trit, x_val 3-trit."""
    w = [0] * 9
    w[8], w[7], w[6], w[5] = opc
    at = value_trits(a_val, 2)   # [d0(w1), d1(w3)]
    w[3], w[4] = at[0], at[1]    # T3 = weight1, T4 = weight3
    xt = value_trits(x_val, 3)   # [e0(w1), e1(w3), e2(w9)]
    w[0], w[1], w[2] = xt
    return w


def _emit_f2(opc3, imm5_val):
    """opc3=(o2,o1,o0), o3=+1; imm5_val 5-trit."""
    w = [0] * 9
    w[8], w[7], w[6], w[5] = POS, opc3[0], opc3[1], opc3[2]
    it = value_trits(imm5_val, 5)
    w[0], w[1], w[2], w[3], w[4] = it
    return w


def _split_ops(line):
    return line.replace(",", " ").split()


def assemble_program(text):
    """Assemble asm source -> (program dict addr->instr9, labels)."""
    # pass 1: labels + instruction list
    items = []
    labels = {}
    addr = 0
    for raw in text.splitlines():
        line = raw.split(";")[0].split("#")[0].strip()
        if not line:
            continue
        while ":" in line:
            name, rest = line.split(":", 1)
            name = name.strip()
            if not name or " " in name:
                break
            if name in labels:
                raise AsmError(f"duplicate label {name}")
            labels[name] = addr
            line = rest.strip()
            if not line:
                break
        if line:
            items.append(line)
            addr += 1

    program = {}
    for i, line in enumerate(items):
        program[i] = _assemble_one(line, i, labels)
    return program, labels


def _operand_b(mn, tok, kind):
    """Return x-field 3-trit value for operand B."""
    if kind == "imm":
        v = _parse_imm(tok)
        if not -13 <= v <= 13:
            raise AsmError(f"{mn}: imm {v} out of 3-trit range")
        return v
    r = _parse_reg(tok)
    return r


def _assemble_one(line, pc, labels):
    parts = _split_ops(line)
    mn = parts[0].upper()
    ops = parts[1:]

    def need(n):
        if len(ops) != n:
            raise AsmError(f"{mn} at {pc}: expected {n} operands, got {len(ops)}")

    if mn in ("ADD", "SUB", "MUL", "MIN", "MAX", "CONS", "ANY", "IS", "CMP"):
        need(2)
        a = _parse_reg(ops[0])
        if not -4 <= a <= 4:
            raise AsmError(f"{mn}: dest {ops[0]} must be active reg -4..4")
        # detect imm vs reg: integer literal -> imm
        try:
            _parse_imm(ops[1])
            is_imm = True
        except AsmError:
            is_imm = False
        kind = "imm" if is_imm else "reg"
        try:
            opc = _opcode_for(mn, kind)
        except AsmError:
            raise AsmError(f"{mn}: no {kind} form (register-only op)")
        x = _operand_b(mn, ops[1], kind)
        return _emit_f1(opc, a, x)

    if mn in ("SHL", "SHR", "RL", "RR"):
        need(2)
        a = _parse_reg(ops[0])
        if not -4 <= a <= 4:
            raise AsmError(f"{mn}: dest must be active reg")
        try:
            _parse_imm(ops[1])
            kind = "shift_imm"
        except AsmError:
            kind = "shift_reg"
        opc = _opcode_for(mn, kind)
        x = _operand_b(mn, ops[1], "imm" if kind == "shift_imm" else "reg")
        return _emit_f1(opc, a, x)

    if mn == "NOP":
        need(0)
        return _emit_f1(_opcode_for("NOP", "nop"), 0, 0)

    if mn == "HALT":
        need(0)
        return _emit_f1(_opcode_for("HALT", "halt"), 0, 0)

    if mn in ("LDI.L", "LDI.M", "LDI.H"):
        need(2)
        a = _parse_reg(ops[0])
        if not -4 <= a <= 4:
            raise AsmError(f"{mn}: dest must be active reg")
        imm = _parse_imm(ops[1])
        if not -13 <= imm <= 13:
            raise AsmError(f"{LDI}: imm out of range".replace("LDI", mn))
        kind = {"LDI.L": "ldi_l", "LDI.M": "ldi_m", "LDI.H": "ldi_h"}[mn]
        return _emit_f1(_opcode_for(mn, kind), a, imm)

    if mn in ("MOV.AG", "MOV.GA", "LDA", "STR"):
        need(2)
        a = _parse_reg(ops[0])
        if not -4 <= a <= 4:
            raise AsmError(f"{mn}: first operand must be active reg")
        x = _parse_reg(ops[1])
        return _emit_f1(_opcode_for(mn, mn.lower().replace(".", "_") if False else _kind_for_misc(mn)), a, x)

    if mn in ("JMP", "JE", "JG", "JL", "JGE", "JNE", "JLE", "JCN", "JCZ", "JCP"):
        need(1)
        tok = ops[0].strip()
        if tok in labels:
            rel = labels[tok] - pc
        else:
            try:
                rel = _parse_imm(tok) - pc if False else None
            except AsmError:
                rel = None
            # numeric operand = absolute target? we define: number = relative offset
            if rel is None:
                try:
                    rel = int(tok, 0)
                except ValueError:
                    raise AsmError(f"{mn}: bad jump operand {tok!r}")
        if not -121 <= rel <= 121:
            raise AsmError(f"{mn} at {pc}: offset {rel} out of 5-trit range")
        opc = _opcode_for(mn, "jump_f2")
        return _emit_f2(opc[1:], rel)

    if mn in ("JZ", "JP", "JN"):
        need(2)
        x = _parse_reg(ops[0])   # general reg tested
        a = _parse_reg(ops[1])   # active reg holding offset
        if not -4 <= a <= 4:
            raise AsmError(f"{mn}: offset reg must be active")
        return _emit_f1(_opcode_for(mn, "jump_reg"), a, x)

    raise AsmError(f"unknown mnemonic {mn} at {pc}")


def _kind_for_misc(mn):
    return {"MOV.AG": "mov_ag", "MOV.GA": "mov_ga", "LDA": "lda", "STR": "str"}[mn]


# ---------------------------------------------------------------------------
# Emulator
# ---------------------------------------------------------------------------

def _wsum(x, y):
    s = x + y
    return s - 3 if s > 1 else (s + 3 if s < -1 else s)


def _cons(x, y):
    return x if x == y else 0


def _anyf(x, y):
    return max(-1, min(1, x + y))


def add9(a, b):
    """Per-trit ternary full adder. a,b: 9-trit lists LSB-first.
    Returns (result9, carry_out)."""
    res = [0] * 9
    cin = 0
    for i in range(9):
        s1 = _wsum(a[i], b[i])
        res[i] = _wsum(s1, cin)
        cin = _anyf(_cons(a[i], b[i]), _cons(s1, cin))
    return res, cin


def sub9(a, b):
    return add9(a, [-t for t in b])


def cmp9(a, b):
    for i in range(8, -1, -1):
        if a[i] > b[i]:
            return 1
        if a[i] < b[i]:
            return -1
    return 0


def shift9(a, amount, mode):
    amount = max(0, min(13, amount))
    if mode in ("rl", "rr"):
        k = amount % 9
        if mode == "rl":
            return [a[(i - k) % 9] for i in range(9)]
        return [a[(i + k) % 9] for i in range(9)]
    if amount >= 9:
        return [0] * 9
    if mode == "shl":
        return [0] * amount + a[:9 - amount]
    return a[amount:] + [0] * amount  # shr


def decode_fields(ins):
    a = trits_value([ins[3], ins[4]])
    x = trits_value([ins[0], ins[1], ins[2]])
    imm5 = trits_value([ins[0], ins[1], ins[2], ins[3], ins[4]])
    return a, x, imm5


class Machine:
    def __init__(self, program, ram_size=27):
        self.mem = dict(program)
        self.ram_size = ram_size
        self.regs = [[0] * 9 for _ in range(27)]
        self.ram = [[0] * 9 for _ in range(ram_size)]
        self.pc = 0
        self.flag = 0
        self.carry = 0
        self.halted = False
        self.steps = 0

    def fetch(self):
        return self.mem.get(self.pc, [0] * 9)

    def step(self):
        if self.halted:
            return
        ins = self.fetch()
        self.steps += 1
        pc_old = self.pc
        op = (ins[8], ins[7], ins[6], ins[5])
        ent = OPCODE_TABLE.get(op)
        if ent is None:
            self.pc += 1
            return
        name, kind = ent
        a_f, x_f, imm5 = decode_fields(ins)
        ai = a_f + 13
        xi = x_f + 13

        def imm9(v3):
            t = value_trits(v3, 3)
            return t + [0] * 6

        next_pc = pc_old + 1

        if kind in ("reg", "imm"):
            b = self.regs[xi] if kind == "reg" else imm9(x_f)
            a = self.regs[ai]
            if name == "ADD":
                self.regs[ai], self.carry = add9(a, b)
            elif name == "SUB":
                self.regs[ai], self.carry = sub9(a, b)
            elif name == "CMP":
                self.flag = cmp9(a, b)
            elif name == "MUL":
                self.regs[ai] = [a[i] * b[i] for i in range(9)]
            elif name == "MIN":
                self.regs[ai] = [min(a[i], b[i]) for i in range(9)]
            elif name == "MAX":
                self.regs[ai] = [max(a[i], b[i]) for i in range(9)]
            elif name == "CONS":
                self.regs[ai] = [a[i] if a[i] == b[i] else 0 for i in range(9)]
            elif name == "ANY":
                self.regs[ai] = [_anyf(a[i], b[i]) for i in range(9)]
            elif name == "IS":
                self.regs[ai] = [1 if a[i] == b[i] else -1 for i in range(9)]
        elif kind in ("shift_reg", "shift_imm"):
            amt = trits_value(self.regs[xi][0:3]) if kind == "shift_reg" else x_f
            self.regs[ai] = shift9(self.regs[ai], amt, name.lower())
        elif kind == "nop":
            pass
        elif kind == "halt":
            self.halted = True
        elif kind in ("ldi_l", "ldi_m", "ldi_h"):
            t3 = value_trits(x_f, 3)
            r = list(self.regs[ai])
            base = {"ldi_l": 0, "ldi_m": 3, "ldi_h": 6}[kind]
            for i in range(3):
                r[base + i] = t3[i]
            if kind == "ldi_l":
                for i in range(3, 9):
                    r[i] = 0
            self.regs[ai] = r
        elif kind == "mov_ag":
            self.regs[ai] = list(self.regs[xi])
        elif kind == "mov_ga":
            self.regs[xi] = list(self.regs[ai])
        elif kind == "lda":
            w = trits_value(self.regs[xi][0:3]) + 13
            self.regs[ai] = list(self.ram[w % self.ram_size])
        elif kind == "str":
            w = trits_value(self.regs[ai][0:3]) + 13
            self.ram[w % self.ram_size] = list(self.regs[xi])
        elif kind == "jump_f2":
            cond = {
                "JMP": True, "JE": self.flag == 0, "JG": self.flag == 1,
                "JL": self.flag == -1, "JGE": self.flag >= 0, "JNE": self.flag != 0,
                "JLE": self.flag <= 0, "JCN": self.carry == -1,
                "JCZ": self.carry == 0, "JCP": self.carry == 1,
            }[name]
            if cond:
                next_pc = pc_old + imm5
        elif kind == "jump_reg":
            tv = cmp9(self.regs[xi], [0] * 9)
            cond = {"JZ": tv == 0, "JP": tv == 1, "JN": tv == -1}[name]
            if cond:
                next_pc = pc_old + trits_value(self.regs[ai])
        self.pc = next_pc


if __name__ == "__main__":
    check_opcode_table()
