"""Cobalt hardware blocks part 2: SHIFT9, DECODE, ALU, CTRL, EXEC,
REGFILE, RAM27, COBALT top.
"""

from chips import ChipBuilder, REGISTRY, nid, chip_pin_ids, pack_trits
from isa import value_trits, OPCODE_TABLE, NEG, ZERO, POS
import csim


def line_name(mn, kind):
    if kind == "reg":
        return mn + "_R"
    if kind == "imm":
        return mn + "_I"
    if kind == "shift_reg":
        return mn + "_R"
    if kind == "shift_imm":
        return mn + "_I"
    return mn.replace(".", "_")


# canonical opcode line order (44 lines)
OPCODE_LINES = [line_name(mn, kind) for opc, (mn, kind) in
                sorted(OPCODE_TABLE.items(), key=lambda kv: kv[0])]
# sort by opcode tuple for determinism
OPCODE_LINES = []
for opc in sorted(OPCODE_TABLE.keys()):
    mn, kind = OPCODE_TABLE[opc]
    OPCODE_LINES.append(line_name(mn, kind))

F2_JUMPS = {"JL", "JE", "JG", "JCN", "JCZ", "JCP", "JMP", "JGE", "JNE", "JLE"}
JREG_JUMPS = {"JN", "JZ", "JP"}
ALU_WRITE_LINES = ["ADD_R", "ADD_I", "SUB_R", "MUL_R", "MIN_R", "MAX_R",
                   "CONS_R", "CONS_I", "ANY_R", "ANY_I", "IS_R", "IS_I",
                   "SHL_R", "SHL_I", "SHR_R", "SHR_I", "RL_R", "RL_I",
                   "RR_R", "RR_I", "LDI_L", "LDI_M", "LDI_H",
                   "MOV_AG", "MOV_GA", "LDA"]
CMP_LINES = ["CMP_R", "CMP_I"]
CARRY_LINES = ["ADD_R", "ADD_I", "SUB_R"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _eq_trit(b, tref, d):
    """+1 iff trit ref == const digit d."""
    g = {POS: "ISP", ZERO: "ISZ", NEG: "ISN"}[d]
    return b.unary(g, tref)


def _max_many(b, refs):
    r = refs[0]
    for t in refs[1:]:
        r = b.binary("MAX", r, t)
    return r


def _min_many(b, refs):
    r = refs[0]
    for t in refs[1:]:
        r = b.binary("MIN", r, t)
    return r


def _const9(b, trits):
    """9-trit const bus from list of 9 trit values -> wide ref."""
    refs = [b.const(t) for t in trits]
    return b.merge1to9(refs)


# ---------------------------------------------------------------------------
# SHIFT9: A9, AMT3 -> SHL9, SHR9, RL9, RR9
# amt decoded via ROM: 3-trit amount (zero-extended) -> trits 0..3 = bits 1,2,4,8
# ---------------------------------------------------------------------------
def _amt_rom_data():
    data = []
    for idx in range(19683):
        v = idx - 9841
        trits = [0] * 9
        if 0 <= v <= 13:
            for i in range(4):
                if v & (1 << i):
                    trits[i] = 1
        data.append(pack_trits(trits))
    return data


def _barrel_stage(b, prev, en, s, direction):
    """one barrel stage: prev = list of 9 refs (LSB first).
    direction: 'shl','shr','rl','rr'. Returns new list of 9 refs."""
    out = []
    for i in range(9):
        if direction == "shl":
            moved = prev[i - s] if i - s >= 0 else b.const(0)
        elif direction == "shr":
            moved = prev[i + s] if i + s < 9 else b.const(0)
        elif direction == "rl":
            moved = prev[(i - s) % 9]
        else:  # rr
            moved = prev[(i + s) % 9]
        out.append(_mux2(b, prev[i], moved, en,
                         label=f"{direction.upper()}{s}.{i}"))
    return out


def _mux2(b, a, bb, sel, label=""):
    """inline MUX2: sel==+1 -> b else a (uses custom MUX2 chip)."""
    m = b.sub("MUX2", label=label)
    mi, mo = chip_pin_ids("MUX2")
    b.wire(a, (m, mi["A"]))
    b.wire(bb, (m, mi["B"]))
    b.wire(sel, (m, mi["SEL"]))
    return (m, mo["OUT"])


def _barrel(b, init_refs, en_bits, direction, reverse_out=False):
    """4-stage barrel. en_bits = [en1,en2,en4,en8]. init_refs = 9 refs."""
    cur = list(init_refs)
    for s, en in zip((1, 2, 4, 8), en_bits):
        cur = _barrel_stage(b, cur, en, s, direction)
    if reverse_out:
        cur = list(reversed(cur))
    return cur


def build_shift9():
    b = ChipBuilder("SHIFT9", colour=(0.3,0.5,0.8,1.0))
    a9 = b.add_input("A", 9)
    amt3 = b.add_input("AMT", 3)
    shl = b.add_output("SHL", 9)
    shr = b.add_output("SHR", 9)
    rl = b.add_output("RL", 9)
    rr = b.add_output("RR", 9)

    ta = b.split9(b.in_ref(a9))
    tamt = b.split3(b.in_ref(amt3))
    # amt3 -> 9-trit address (low 3 trits, rest 0)
    z6 = [b.const(0)] * 6
    amt9 = b.merge1to9(tamt + z6)
    rom = b.sub("ROM 19683x9", internal=_amt_rom_data(), label="AMT_LUT")
    rin, rout = _rom_pins()
    b.wire(amt9, (rom, rin))
    rsplit = b.split9((rom, rout))
    en_bits = rsplit[0:4]  # trits 0..3 = bits 1,2,4,8

    rev = [ta[8 - i] for i in range(9)]

    shl_r = _barrel(b, ta, en_bits, "shl")
    shr_r = _barrel(b, rev, en_bits, "shl", reverse_out=True)
    rl_r = _barrel(b, ta, en_bits, "rl")
    rr_r = _barrel(b, rev, en_bits, "rl", reverse_out=True)

    for out_pin, refs, nm in ((shl, shl_r, "SHL"), (shr, shr_r, "SHR"),
                              (rl, rl_r, "RL"), (rr, rr_r, "RR")):
        bus = b.merge1to9(refs, label=nm)
        b.wire(bus, b.out_ref(out_pin))
    return b.register()


def _rom_pins():
    return 0, 1  # ROM 19683x9: ADDRESS id0, DATA id1


# ---------------------------------------------------------------------------
# DECODE: INSTR9 -> 44 opcode lines + IMM_MODE + SHIFT_IMM_MODE
# ---------------------------------------------------------------------------
def build_decode():
    b = ChipBuilder("DECODE", colour=(0.75,0.35,0.35,1.0))
    ins = b.add_input("INSTR", 9)
    line_pins = {}
    for ln in OPCODE_LINES:
        line_pins[ln] = b.add_output(ln, 1)
    imm_mode = b.add_output("IMM_MODE", 1)
    simm = b.add_output("SHIFT_IMM", 1)

    t = b.split9(b.in_ref(ins))
    # opcode trits: T8=o3,T7=o2,T6=o1,T5=o0 at indices 8,7,6,5
    opt = [t[8], t[7], t[6], t[5]]
    for opc in sorted(OPCODE_TABLE.keys()):
        mn, kind = OPCODE_TABLE[opc]
        ln = line_name(mn, kind)
        # eq per trit: opt[0]=o3 at T8, opt[1]=o2 T7, opt[2]=o1 T6, opt[3]=o0 T5
        eqs = [_eq_trit(b, opt[j], opc[j]) for j in range(4)]
        e = _min_many(b, eqs)
        line = b.unary("CLU", e, label=ln)
        b.wire(line, b.out_ref(line_pins[ln]))

    imm_lines = [line_pins[l] for l in
                 ("ADD_I", "CONS_I", "ANY_I", "IS_I", "CMP_I",
                  "SHL_I", "SHR_I", "RL_I", "RR_I")]
    b.wire(_max_many(b, [b.in_ref(p) for p in imm_lines]), b.out_ref(imm_mode))
    simm_lines = [line_pins[l] for l in ("SHL_I", "SHR_I", "RL_I", "RR_I")]
    b.wire(_max_many(b, [b.in_ref(p) for p in simm_lines]), b.out_ref(simm))
    return b.register()


# ---------------------------------------------------------------------------
# ALU: RA9,RB9,IMM3,RAMD9,IMM_MODE,SHIFT_IMM,44 op lines -> RES9,FLAG,CARRY
# ---------------------------------------------------------------------------
def build_alu():
    b = ChipBuilder("ALU", colour=(0.25,0.55,0.75,1.0))
    ra = b.add_input("RA", 9)
    rb = b.add_input("RB", 9)
    imm3 = b.add_input("IMM", 3)
    ramd = b.add_input("RAMD", 9)
    imm_mode = b.add_input("IMM_MODE", 1)
    simm = b.add_input("SHIFT_IMM", 1)
    res = b.add_output("RES", 9)
    flag = b.add_output("FLAG", 1)
    carry = b.add_output("CARRY", 1)
    line_pins = {}
    for ln in OPCODE_LINES:
        line_pins[ln] = b.add_input(ln, 1)

    ta = b.split9(b.in_ref(ra))
    tb = b.split9(b.in_ref(rb))
    ti = b.split3(b.in_ref(imm3))
    tr = b.split9(b.in_ref(ramd))

    # imm9 bus: imm trits low3, zeros high6
    imm9 = b.merge1to9(ti + [b.const(0)] * 6)
    # B9 = IMM_MODE ? imm9 : RB9  (per trit)
    tb9 = b.split9(b.in_ref(rb))
    ti9 = b.split9(imm9)
    bsel = b.in_ref(imm_mode)
    b9refs = [_mux2(b, tb9[i], ti9[i], bsel) for i in range(9)]
    b9 = b.merge1to9(b9refs)

    # arithmetic
    ad = b.sub("ADDER9", x=-14, y=5, label="ADD")
    ain, aout = chip_pin_ids("ADDER9")
    b.wire(b.in_ref(ra), (ad, ain["A"]))
    b.wire(b9, (ad, ain["B"]))
    add_sum = (ad, aout["SUM"])
    add_co = (ad, aout["CO"])

    sb = b.sub("SUB9", x=-11, y=5, label="SUB")
    sin, sout = chip_pin_ids("SUB9")
    b.wire(b.in_ref(ra), (sb, sin["A"]))
    b.wire(b9, (sb, sin["B"]))
    sub_sum = (sb, sout["SUM"])
    sub_co = (sb, sout["CO"])

    cp = b.sub("CMP9", x=-8, y=5, label="CMP→FLAG")
    cin_, cout = chip_pin_ids("CMP9")
    b.wire(b.in_ref(ra), (cp, cin_["A"]))
    b.wire(b9, (cp, cin_["B"]))
    fl = (cp, cout["FL"])
    b.wire(fl, b.out_ref(flag))

    # carry = SUB ? sub_co : add_co
    sub_line = b.in_ref(line_pins["SUB_R"])
    car = _mux2(b, add_co, sub_co, sub_line)
    b.wire(car, b.out_ref(carry))

    # trit-wise ops
    tw = {}
    for k, (nm, chip) in enumerate((("MIN", "MIN9"), ("MAX", "MAX9"), ("MUL", "MUL9"),
                     ("CONS", "CONS9"), ("ANY", "ANY9"), ("IS", "IS9"))):
        s = b.sub(chip, x=-14 + k * 3, y=-5, label=nm)
        pin = chip_pin_ids(chip)
        b.wire(b.in_ref(ra), (s, pin[0]["A"]))
        b.wire(b9, (s, pin[0]["B"]))
        tw[nm] = (s, pin[1]["OUT"])

    # shifter: AMT3 = SHIFT_IMM ? IMM3 : RB9[0:3]
    amt_refs = []
    for i in range(3):
        amt_refs.append(_mux2(b, tb[i], ti[i], b.in_ref(simm)))
    amt3 = b.merge1to3(amt_refs)
    sh = b.sub("SHIFT9", x=4, y=0, label="SHIFT")
    shin, shout = chip_pin_ids("SHIFT9")
    b.wire(b.in_ref(ra), (sh, shin["A"]))
    b.wire(amt3, (sh, shin["AMT"]))
    shl = (sh, shout["SHL"])
    shr = (sh, shout["SHR"])
    rl = (sh, shout["RL"])
    rr = (sh, shout["RR"])

    # LDI buses (pure wiring)
    z = b.const(0)
    ldi_l = b.merge1to9([ti[0], ti[1], ti[2], z, z, z, z, z, z])
    ldi_m = b.merge1to9([ta[0], ta[1], ta[2], ti[0], ti[1], ti[2], ta[6], ta[7], ta[8]])
    ldi_h = b.merge1to9([ta[0], ta[1], ta[2], ta[3], ta[4], ta[5], ti[0], ti[1], ti[2]])

    # candidates: name -> 9-trit wide ref
    cand = {
        "ADD": add_sum, "SUB": sub_sum,
        "MUL": tw["MUL"], "MIN": tw["MIN"], "MAX": tw["MAX"],
        "CONS": tw["CONS"], "ANY": tw["ANY"], "IS": tw["IS"],
        "SHL": shl, "SHR": shr, "RL": rl, "RR": rr,
        "LDI_L": ldi_l, "LDI_M": ldi_m, "LDI_H": ldi_h,
        "MOV_AG": b.in_ref(rb), "LDA": b.in_ref(ramd), "MOV_GA": b.in_ref(ra),
    }

    # enable per candidate = OR of relevant op lines
    def en(*lns):
        return _max_many(b, [b.in_ref(line_pins[l]) for l in lns])

    enables = {
        "ADD": en("ADD_R", "ADD_I"),
        "SUB": en("SUB_R"),
        "MUL": en("MUL_R"),
        "MIN": en("MIN_R"),
        "MAX": en("MAX_R"),
        "CONS": en("CONS_R", "CONS_I"),
        "ANY": en("ANY_R", "ANY_I"),
        "IS": en("IS_R", "IS_I"),
        "SHL": en("SHL_R", "SHL_I"),
        "SHR": en("SHR_R", "SHR_I"),
        "RL": en("RL_R", "RL_I"),
        "RR": en("RR_R", "RR_I"),
        "LDI_L": en("LDI_L"),
        "LDI_M": en("LDI_M"),
        "LDI_H": en("LDI_H"),
        "MOV_AG": en("MOV_AG"),
        "LDA": en("LDA"),
        "MOV_GA": en("MOV_GA"),
    }

    # per-trit TS mux: for each trit i, each candidate -> TS(EN=en) -> net -> merge
    cand_trits = {}
    for nm, ref in cand.items():
        cand_trits[nm] = b.split9(ref)
    # merge "1-9TRIT": input pin id = 8-i carries trit i; output pin id 9
    mg = b.sub("1-9TRIT")
    for i in range(9):
        for nm in cand:
            sid = b.sub("3-STATE BUFFER")
            b.wire(cand_trits[nm][i], (sid, 0))
            b.wire(enables[nm], (sid, 1))
            b.wire((sid, 2), (mg, 8 - i))
    b.wire((mg, 9), b.out_ref(res))
    return b.register()


# ---------------------------------------------------------------------------
# CTRL: INSTR9, 44 lines, FLAG, CARRY, RA9, RB9, PC9 ->
#   NEXTPC9, WR_EN, DEST_X, WR_ADDR3, FLAG_WE, CARRY_WE, RAM_WE, RAM_ADDR3, HALT
# ---------------------------------------------------------------------------
def build_ctrl():
    b = ChipBuilder("CTRL", colour=(0.75,0.4,0.3,1.0))
    ins = b.add_input("INSTR", 9)
    flag = b.add_input("FLAG", 1)
    carry = b.add_input("CARRY", 1)
    ra = b.add_input("RA", 9)
    rb = b.add_input("RB", 9)
    pc = b.add_input("PC", 9)
    npc = b.add_output("NEXTPC", 9)
    wr_en = b.add_output("WR_EN", 1)
    dest_x = b.add_output("DEST_X", 1)
    wr_addr = b.add_output("WR_ADDR", 3)
    flag_we = b.add_output("FLAG_WE", 1)
    carry_we = b.add_output("CARRY_WE", 1)
    ram_we = b.add_output("RAM_WE", 1)
    ram_addr = b.add_output("RAM_ADDR", 3)
    halt = b.add_output("HALT", 1)
    line_pins = {}
    for ln in OPCODE_LINES:
        line_pins[ln] = b.add_input(ln, 1)

    t = b.split9(b.in_ref(ins))
    tra = b.split9(b.in_ref(ra))
    trb = b.split9(b.in_ref(rb))

    def L(ln):
        return b.in_ref(line_pins[ln])

    # ---- next PC ----
    # imm5 -> 9tr (trits 0..4 = T0..T4, rest 0)
    imm5 = b.merge1to9([t[0], t[1], t[2], t[3], t[4], b.const(0), b.const(0), b.const(0), b.const(0)])
    one9 = _const9(b, [1, 0, 0, 0, 0, 0, 0, 0, 0])
    zero9 = _const9(b, [0] * 9)

    # X-test: CMP9(RB9, 0)
    xt = b.sub("CMP9", x=-5, y=4, label="X-TEST")
    xin, xout = chip_pin_ids("CMP9")
    b.wire(b.in_ref(rb), (xt, xin["A"]))
    b.wire(zero9, (xt, xin["B"]))
    xtest = (xt, xout["FL"])

    # jump conditions
    f = b.in_ref(flag)
    c = b.in_ref(carry)
    xf = xtest
    conds = {
        "JL": b.unary("ISN", f), "JE": b.unary("ISZ", f), "JG": b.unary("ISP", f),
        "JGE": b.unary("NOT", b.unary("ISN", f)),
        "JNE": b.unary("NOT", b.unary("ISZ", f)),
        "JLE": b.unary("NOT", b.unary("ISP", f)),
        "JCN": b.unary("ISN", c), "JCZ": b.unary("ISZ", c), "JCP": b.unary("ISP", c),
        "JMP": b.const(1),
        "JN": b.unary("ISN", xf), "JZ": b.unary("ISZ", xf), "JP": b.unary("ISP", xf),
    }
    contribs = []
    for opc in sorted(OPCODE_TABLE.keys()):
        mn, kind = OPCODE_TABLE[opc]
        if kind in ("jump_f2", "jump_reg"):
            contribs.append(b.binary("MIN", L(mn), conds[mn]))
    taken = _max_many(b, contribs)

    # OFF_FINAL = TAKEN ? (IS_F2 ? IMM5 : RA9) : ONE9   per trit
    is_f2 = _max_many(b, [L(mn) for mn in F2_JUMPS])
    ti5 = b.split9(imm5)
    tra9 = b.split9(b.in_ref(ra))
    tone = b.split9(one9)
    off_refs = []
    for i in range(9):
        inner = _mux2(b, tra9[i], ti5[i], is_f2)      # F2? imm5 : RA9
        off_refs.append(_mux2(b, tone[i], inner, taken))  # taken? inner : 1
    off9 = b.merge1to9(off_refs)

    adp = b.sub("ADDER9", x=5, y=4, label="NEXTPC")
    ain, aout = chip_pin_ids("ADDER9")
    b.wire(b.in_ref(pc), (adp, ain["A"]))
    b.wire(off9, (adp, ain["B"]))
    b.wire((adp, aout["SUM"]), b.out_ref(npc))

    # ---- write controls ----
    wr = _max_many(b, [L(l) for l in ALU_WRITE_LINES])
    b.wire(wr, b.out_ref(wr_en))
    dx = L("MOV_GA")
    b.wire(dx, b.out_ref(dest_x))

    # WR_ADDR3 = DEST_X ? X3 : AEXT3
    # AEXT3 digits: d0=T3,d1=T4,d2=0 ; X3: d0=T0,d1=T1,d2=T2
    aext = [t[3], t[4], b.const(0)]
    x3 = [t[0], t[1], t[2]]
    wa_refs = [_mux2(b, aext[i], x3[i], dx) for i in range(3)]
    wa3 = b.merge1to3(wa_refs)
    b.wire(wa3, b.out_ref(wr_addr))

    fwe = _max_many(b, [L(l) for l in CMP_LINES])
    b.wire(fwe, b.out_ref(flag_we))
    cwe = _max_many(b, [L(l) for l in CARRY_LINES])
    b.wire(cwe, b.out_ref(carry_we))

    rw = L("STR")
    b.wire(rw, b.out_ref(ram_we))
    # RAM_ADDR3 = STR ? RA9[0:3] : RB9[0:3]
    ra3 = [_mux2(b, trb[i], tra[i], rw) for i in range(3)]
    ram3 = b.merge1to3(ra3)
    b.wire(ram3, b.out_ref(ram_addr))

    b.wire(L("HALT"), b.out_ref(halt))
    return b.register()


# ---------------------------------------------------------------------------
# EXEC: INSTR9,RA9,RB9,RAMD9,PC9,FLAG,CARRY,EXEC_EN ->
#   stage bundle outputs (registered by MEMs)
# ---------------------------------------------------------------------------
def build_exec():
    b = ChipBuilder("EXEC", colour=(0.8,0.5,0.25,1.0))
    ins = b.add_input("INSTR", 9)
    ra = b.add_input("RA", 9)
    rb = b.add_input("RB", 9)
    ramd = b.add_input("RAMD", 9)
    pc = b.add_input("PC", 9)
    flag = b.add_input("FLAG", 1)
    carry = b.add_input("CARRY", 1)
    een = b.add_input("EXEC_EN", 1)

    dec = b.sub("DECODE", x=-9, y=4, label="DECODE")
    din, dout = chip_pin_ids("DECODE")
    b.wire(b.in_ref(ins), (dec, din["INSTR"]))

    alu = b.sub("ALU", x=-9, y=-4, label="ALU")
    ain, aout = chip_pin_ids("ALU")
    b.wire(b.in_ref(ra), (alu, ain["RA"]))
    b.wire(b.in_ref(rb), (alu, ain["RB"]))
    # IMM3 = INSTR trits 0..2 -> merge1to3
    ti = b.split9(b.in_ref(ins))
    imm3 = b.merge1to3([ti[0], ti[1], ti[2]])
    b.wire(imm3, (alu, ain["IMM"]))
    b.wire(b.in_ref(ramd), (alu, ain["RAMD"]))
    b.wire((dec, dout["IMM_MODE"]), (alu, ain["IMM_MODE"]))
    b.wire((dec, dout["SHIFT_IMM"]), (alu, ain["SHIFT_IMM"]))
    for ln in OPCODE_LINES:
        b.wire((dec, dout[ln]), (alu, ain[ln]))

    ctrl = b.sub("CTRL", x=5, y=0, label="CTRL")
    cin_, cout = chip_pin_ids("CTRL")
    b.wire(b.in_ref(ins), (ctrl, cin_["INSTR"]))
    for ln in OPCODE_LINES:
        b.wire((dec, dout[ln]), (ctrl, cin_[ln]))
    b.wire(b.in_ref(flag), (ctrl, cin_["FLAG"]))
    b.wire(b.in_ref(carry), (ctrl, cin_["CARRY"]))
    b.wire(b.in_ref(ra), (ctrl, cin_["RA"]))
    b.wire(b.in_ref(rb), (ctrl, cin_["RB"]))
    b.wire(b.in_ref(pc), (ctrl, cin_["PC"]))

    # ---- stage MEMs: capture bundle during EXEC ----
    een_ref = b.in_ref(een)

    def stage1(sig, out_pin, label=""):
        m = b.sub("MEM 1TRIT", label=label)
        b.wire(sig, (m, 0))       # DATA in
        b.wire(een_ref, (m, 1))   # WE
        b.wire((m, 2), b.out_ref(out_pin))

    def stage_bus(signals, out_pin, n, label=""):
        refs = []
        for i, s in enumerate(signals):
            m = b.sub("MEM 1TRIT", label=f"{label}{i}" if label else "")
            b.wire(s, (m, 0))
            b.wire(een_ref, (m, 1))
            refs.append((m, 2))
        bus = b.merge1to9(refs) if n == 9 else b.merge1to3(refs)
        b.wire(bus, b.out_ref(out_pin))

    s_nextpc = b.add_output("S_NEXTPC", 9)
    s_wrdata = b.add_output("S_WRDATA", 9)
    s_wraddr = b.add_output("S_WRADDR", 3)
    s_wren = b.add_output("S_WR_EN", 1)
    s_destx = b.add_output("S_DEST_X", 1)
    s_fwe = b.add_output("S_FLAG_WE", 1)
    s_fdata = b.add_output("S_FLAG_DATA", 1)
    s_cwe = b.add_output("S_CARRY_WE", 1)
    s_cdata = b.add_output("S_CARRY_DATA", 1)
    s_rwe = b.add_output("S_RAM_WE", 1)
    s_raddr = b.add_output("S_RAM_ADDR", 3)
    s_halt = b.add_output("S_HALT", 1)

    # signals (1-trit refs) from ALU/CTRL wide outputs -> split
    def wide_trits(ref, n):
        if n == 1:
            return [ref]
        return b.split9(ref) if n == 9 else b.split3(ref)

    npc_t = wide_trits((ctrl, cout["NEXTPC"]), 9)
    wrd_t = wide_trits((alu, aout["RES"]), 9)
    wra_t = wide_trits((ctrl, cout["WR_ADDR"]), 3)
    fla_t = wide_trits((alu, aout["FLAG"]), 1)
    cra_t = wide_trits((alu, aout["CARRY"]), 1)
    raa_t = wide_trits((ctrl, cout["RAM_ADDR"]), 3)

    stage_bus(npc_t, s_nextpc, 9, "NEXTPC")
    stage_bus(wrd_t, s_wrdata, 9, "WRDATA")
    stage_bus(wra_t, s_wraddr, 3, "WRADDR")
    stage1((ctrl, cout["WR_EN"]), s_wren, "WR_EN")
    stage1((ctrl, cout["DEST_X"]), s_destx, "DEST_X")
    stage1((ctrl, cout["FLAG_WE"]), s_fwe, "FLAG_WE")
    stage1(fla_t[0], s_fdata, "FLAG_DATA")
    stage1((ctrl, cout["CARRY_WE"]), s_cwe, "CARRY_WE")
    stage1(cra_t[0], s_cdata, "CARRY_DATA")
    stage1((ctrl, cout["RAM_WE"]), s_rwe, "RAM_WE")
    stage_bus(raa_t, s_raddr, 3, "RAM_ADDR")
    stage1((ctrl, cout["HALT"]), s_halt, "HALT")
    return b.register()


# ---------------------------------------------------------------------------
# REGFILE: WR_ADDR3,WR_DATA9,WR_EN,RA_SEL3,RB_SEL3,RESET -> RA9,RB9,MON0..26
# regs r-13..r13 (idx 0..26), active = idx 9..17
# ---------------------------------------------------------------------------
def _dec3(b, addr_trits, values, prefix=""):
    """addr_trits: 3 1-trit refs (d0,d1,d2 LSB first). values: list of ints.
    Returns dict value->line ref (+1 iff addr==value)."""
    lines = {}
    for v in values:
        digs = value_trits(v, 3)  # LSB first [d0,d1,d2]
        eqs = [_eq_trit(b, addr_trits[i], digs[i]) for i in range(3)]
        e = _min_many(b, eqs)
        lines[v] = b.unary("CLU", e, label=f"{prefix}{v}")
    return lines


def _dec2_as3(b, addr_trits, values):
    """decode 3-trit addr but only for small range (same as _dec3)."""
    return _dec3(b, addr_trits, values)


def build_regfile():
    b = ChipBuilder("REGFILE", colour=(0.35,0.65,0.4,1.0))
    wa = b.add_input("WR_ADDR", 3)
    wd = b.add_input("WR_DATA", 9)
    wen = b.add_input("WR_EN", 1)
    ra_sel = b.add_input("RA_SEL", 3)
    rb_sel = b.add_input("RB_SEL", 3)
    rst = b.add_input("RESET", 1)
    ra9 = b.add_output("RA", 9)
    rb9 = b.add_output("RB", 9)
    mons = [b.add_output(f"MON{k}", 9) for k in range(27)]  # MONk <-> reg idx k (v=k-13)

    twa = b.split3(b.in_ref(wa))
    tra = b.split3(b.in_ref(ra_sel))
    trb = b.split3(b.in_ref(rb_sel))
    twd = b.split9(b.in_ref(wd))

    wen_ref = b.in_ref(wen)
    rst_sel = b.unary("ISP", b.in_ref(rst))        # +1 iff RESET==+1
    rq = b.unary("CLU", rst_sel)                   # 0/+1 reset-qualified
    # reset writes 0: mux WR_DATA trits to const0 during reset.
    # WE term and DATA select share rq -> consistent (DATA,WE) pair per MEM.
    wd_eff = []
    for i in range(9):
        wd_eff.append(_mux2(b, twd[i], b.const(0), rq))

    # decoders
    wlines = _dec3(b, twa, list(range(-13, 14)), "W")     # 27 write lines
    rblines = _dec3(b, trb, list(range(-13, 14)), "RB")   # 27 readB lines
    ralines = _dec3(b, tra, list(range(-4, 5)), "RA")     # 9 readA lines

    # storage: reg idx j (0..26) value v=j-13
    # WE = MAX(MIN(WR_EN,line), RESET) ; DATA = reset?0:WR_DATA
    reg_trits = {}   # (j,i) -> MEM out ref
    for j in range(27):
        v = j - 13
        we_pos = b.binary("MIN", wen_ref, wlines[v])
        we = b.binary("MAX", we_pos, rq)
        outs = []
        for i in range(9):
            m = b.mem(label=f"R{v}.{i}")
            b.wire(wd_eff[i], (m, 0))
            b.wire(we, (m, 1))
            outs.append((m, 2))
        reg_trits[j] = outs

    # readA: regs 9..17 -> trit nets -> merge -> RA9
    def read_port(sel_lines, reg_indices):
        # returns 9 trit refs (narrow) for the bus
        bus_trits = []
        for i in range(9):
            drivers = []
            for k, j in enumerate(reg_indices):
                v = j - 13
                if v in sel_lines:
                    sid = b.sub("3-STATE BUFFER")
                    b.wire(reg_trits[j][i], (sid, 0))
                    b.wire(sel_lines[v], (sid, 1))
                    drivers.append((sid, 2))
            bus_trits.append(drivers)
        return bus_trits

    # for merge we need single ref per trit; multiple drivers wire to same pin
    def merge_driven(bus_trits, out_pin, label=""):
        # "1-9TRIT": input pin id = 8-i carries trit i; output pin id 9
        mg = b.sub("1-9TRIT", label=label)
        for i in range(9):
            for d in bus_trits[i]:
                b.wire(d, (mg, 8 - i))
        b.wire((mg, 9), b.out_ref(out_pin))

    ra_bus = read_port(ralines, list(range(9, 18)))
    merge_driven(ra_bus, ra9, "RA")
    rb_bus = read_port(rblines, list(range(27)))
    merge_driven(rb_bus, rb9, "RB")

    # monitor outputs: all 27 regs -> MON0..26 (MONk <-> reg idx k)
    for k in range(27):
        bus = b.merge1to9(reg_trits[k])
        b.wire(bus, b.out_ref(mons[k]))
    return b.register()


# ---------------------------------------------------------------------------
# RAM27: ADDR3,WDATA9,WEN,RESET -> DOUT9   (27 words x 9 trits)
# ---------------------------------------------------------------------------
def build_ram27():
    b = ChipBuilder("RAM27", colour=(0.3,0.6,0.55,1.0))
    ad = b.add_input("ADDR", 3)
    wd = b.add_input("WDATA", 9)
    wen = b.add_input("WEN", 1)
    rst = b.add_input("RESET", 1)
    dout = b.add_output("DOUT", 9)

    ta = b.split3(b.in_ref(ad))
    twd = b.split9(b.in_ref(wd))
    wen_ref = b.in_ref(wen)
    rst_sel = b.unary("ISP", b.in_ref(rst))
    rq = b.unary("CLU", rst_sel)
    wd_eff = [_mux2(b, twd[i], b.const(0), rq) for i in range(9)]

    lines = _dec3(b, ta, list(range(-13, 14)), "A")
    reg_trits = {}
    for j in range(27):
        v = j - 13
        we_pos = b.binary("MIN", wen_ref, lines[v])
        we = b.binary("MAX", we_pos, rq)
        outs = []
        for i in range(9):
            m = b.mem(label=f"RAM{v}.{i}")
            b.wire(wd_eff[i], (m, 0))
            b.wire(we, (m, 1))
            outs.append((m, 2))
        reg_trits[j] = outs

    bus_trits = []
    for i in range(9):
        drivers = []
        for j in range(27):
            v = j - 13
            sid = b.sub("3-STATE BUFFER")
            b.wire(reg_trits[j][i], (sid, 0))
            b.wire(lines[v], (sid, 1))
            drivers.append((sid, 2))
        bus_trits.append(drivers)
    mg = b.sub("1-9TRIT", label="DOUT")
    for i in range(9):
        for d in bus_trits[i]:
            b.wire(d, (mg, 8 - i))
    b.wire((mg, 9), b.out_ref(dout))
    return b.register()


# ---------------------------------------------------------------------------
# COBALT top
# ---------------------------------------------------------------------------
def build_cobalt(program):
    """program: dict addr->instr9 (from isa.assemble_program)."""
    b = ChipBuilder("COBALT", colour=(0.2, 0.4, 0.8, 1.0))
    rst = b.add_input("RESET", 1)
    mode = b.add_input("MODE", 1)   # +1 = auto, else manual
    step = b.add_input("STEP", 1)
    ins_in = b.add_input("INSTR", 9)  # fetched instruction word (external ROM)

    pc9 = b.add_output("PC", 9)
    flags = b.add_output("FLAG", 1)
    carry = b.add_output("CARRY", 1)
    phase = b.add_output("PHASE", 1)
    halted = b.add_output("HALTED", 1)
    mon_pins = [b.add_output(f"R{k - 13}", 9) for k in range(27)]  # R-13..R13

    # ---- fetch: instruction comes from the INSTR input pin (external ROM) ----
    # ---- PH generator ----
    # BOOT MEM: init 0 (trit -1), D=+1, WE=+1 -> becomes +1 after frame 1.
    # boot_ok = ISP(BOOT) clamped -> 0 on frame1 (incl. disconnected fallback),
    # +1 afterwards. Gates WE_PH so PH holds its -1 init through frame 1 and
    # can never latch the absorbing PH=0 state.
    boot = b.mem(init=0, x=-27, y=-2, label="BOOT")
    b.wire(b.const(1), (boot, 0))
    b.wire(b.const(1), (boot, 1))
    boot_out = (boot, 2)
    boot_ok = b.unary("CLU", b.unary("ISP", boot_out))

    # PH MEM: init -1 (InternalData=[0]); DATA = RESET? -1 : toggle(PH)
    # toggle(PH) = MAX(NOT(PH), ISZ(NOT(PH))) : -1<->+1, and 0 -> +1 (recovers
    # from the absorbing zero state instead of sticking).
    ph = b.mem(init=0, x=-24, y=-2, label="PHASE")
    ph_out = (ph, 2)
    ph_not = b.unary("NOT", ph_out)
    ph_tgl = b.binary("MAX", ph_not, b.unary("ISZ", ph_not))
    rst_isp = b.unary("ISP", b.in_ref(rst))
    rq = b.unary("CLU", rst_isp)              # reset-qualified 0/+1
    ph_data = _mux2(b, ph_tgl, b.const(-1), rq)
    # PH.WE = MIN( MAX(we_src, reset_bit), boot_ok )
    # we_src = MODE==+1 ? auto_pulse : step_pulse
    # auto_pulse = PULSE(CLOCK,1): one 1-frame pulse per 500-frame clock
    # period -> PH holds ~500 frames per phase so wb_pos is stable all frame
    # and CUR writes are atomic. Manual STEP gives the same narrow pulse.
    step_pulse = b.sub("PULSE", internal=[1, 0, 0])
    spin, spout = 0, 1
    b.wire(b.in_ref(step), (step_pulse, spin))
    clk = b.sub("CLOCK")
    auto_pulse = b.sub("PULSE", internal=[1, 0, 0])
    b.wire((clk, 0), (auto_pulse, 0))
    auto_sel = b.unary("ISP", b.in_ref(mode))   # +1 iff MODE==+1
    we_src = _mux2(b, (step_pulse, spout), (auto_pulse, 1), auto_sel)
    we1 = b.binary("MAX", we_src, rq)
    we_ph = b.binary("MIN", we1, boot_ok)
    b.wire(ph_data, (ph, 0))
    b.wire(we_ph, (ph, 1))
    b.wire(ph_out, b.out_ref(phase))

    # EXEC_EN = CLU(ISN(PH)) -> +1 iff PH==-1 else 0 (never -1: stage WE must
    # be 0/+1 so stage holds during WB instead of being cleared)
    exec_en = b.unary("CLU", b.unary("ISN", ph_out))
    wb_pos = b.unary("CLU", b.unary("ISP", ph_out))

    # ---- PC register (9 MEMs) ----
    # PC storage MEMs; WE = RESET?-1 : WB_pos ; DATA = S_NEXTPC
    # PC9 bus = merge of MEM outputs
    # PC starts at -9841 (all trits -1) so PC value == ROM row index:
    # program occupies ROM cells 0..n instead of the signed-offset middle.
    pc_mem_refs = []
    for i in range(9):
        m = b.mem(init=0, x=-21, y=12 - i * 1.1, label=f"PC{i}")
        pc_mem_refs.append((m, 2))
    pc_bus = b.merge1to9(pc_mem_refs, x=-17.5, y=8, label="PC")
    b.wire(pc_bus, b.out_ref(pc9))

    # ---- INSTR ----
    ins_bus = b.in_ref(ins_in)
    ti = b.split9(ins_bus, x=-16, y=10, label="INSTR")
    ra_sel = b.merge1to3([ti[3], ti[4], b.const(0)], x=-13, y=10, label="RA_SEL")
    rb_sel = b.merge1to3([ti[0], ti[1], ti[2]], x=-13, y=7.5, label="RB_SEL")

    # ---- REGFILE ----
    rf = b.sub("REGFILE", x=-6, y=5, label="REGFILE")
    rfi, rfo = chip_pin_ids("REGFILE")
    # WR_* come from EXEC stage outputs (wired later)
    b.wire(ra_sel, (rf, rfi["RA_SEL"]))
    b.wire(rb_sel, (rf, rfi["RB_SEL"]))
    b.wire(b.in_ref(rst), (rf, rfi["RESET"]))

    # ---- RAM27 ----
    ram = b.sub("RAM27", x=-6, y=-4, label="RAM27")
    rami, ramo = chip_pin_ids("RAM27")
    b.wire(b.in_ref(rst), (ram, rami["RESET"]))

    # ---- EXEC ----
    ex = b.sub("EXEC", x=8, y=0, label="EXEC")
    exi, exo = chip_pin_ids("EXEC")
    b.wire(ins_bus, (ex, exi["INSTR"]))
    b.wire((rf, rfo["RA"]), (ex, exi["RA"]))
    b.wire((rf, rfo["RB"]), (ex, exi["RB"]))
    b.wire((ram, ramo["DOUT"]), (ex, exi["RAMD"]))
    b.wire(pc_bus, (ex, exi["PC"]))
    # FLAG/CARRY come from flag/carry MEMs (below) - need refs first
    # create flag/carry/halt MEMs now
    fl = b.mem(init=1, x=-13, y=-1, label="FLAG")   # flag init 0 (uint 1)
    ca = b.mem(init=1, x=-10, y=-1, label="CARRY")  # carry init 0
    ha = b.mem(init=1, x=-7, y=-1, label="HALT")    # halt init 0
    fl_out, ca_out, ha_out = (fl, 2), (ca, 2), (ha, 2)
    b.wire(fl_out, b.out_ref(flags))
    b.wire(ca_out, b.out_ref(carry))
    b.wire(ha_out, b.out_ref(halted))
    b.wire(fl_out, (ex, exi["FLAG"]))
    b.wire(ca_out, (ex, exi["CARRY"]))
    b.wire(exec_en, (ex, exi["EXEC_EN"]))

    # ---- WB routing: stage -> CUR ----
    # stage outputs are EXEC output pins; split wide ones
    s_wren = (ex, exo["S_WR_EN"])
    s_destx = (ex, exo["S_DEST_X"])
    s_fwe = (ex, exo["S_FLAG_WE"])
    s_cwe = (ex, exo["S_CARRY_WE"])
    s_rwe = (ex, exo["S_RAM_WE"])
    s_halt = (ex, exo["S_HALT"])
    s_wrdata = b.split9((ex, exo["S_WRDATA"]))
    s_wraddr = b.split3((ex, exo["S_WRADDR"]))
    s_nextpc = b.split9((ex, exo["S_NEXTPC"]))
    s_fdata = (ex, exo["S_FLAG_DATA"])
    s_cdata = (ex, exo["S_CARRY_DATA"])
    s_raddr = b.split3((ex, exo["S_RAM_ADDR"]))

    # effective write enables (WB phase only)
    def wb_and(sig):
        return b.binary("MIN", sig, wb_pos)   # sig,wb_pos in {0,+1} -> 0/+1

    wr_en_eff = wb_and(s_wren)
    # REGFILE: WR_EN = wr_en_eff ; WR_ADDR3 = stage wr_addr ; WR_DATA9 = stage wr_data
    wr_addr3 = b.merge1to3(s_wraddr)
    wr_data9 = b.merge1to9(s_wrdata)
    b.wire(wr_en_eff, (rf, rfi["WR_EN"]))
    b.wire(wr_addr3, (rf, rfi["WR_ADDR"]))
    b.wire(wr_data9, (rf, rfi["WR_DATA"]))

    # RAM: WEN = RAM_WE & WB ; ADDR = stage ram_addr ; WDATA = RB9 (X reg)
    ram_wen = wb_and(s_rwe)
    ram_addr3 = b.merge1to3(s_raddr)
    b.wire(ram_wen, (ram, rami["WEN"]))
    b.wire(ram_addr3, (ram, rami["ADDR"]))
    b.wire((rf, rfo["RB"]), (ram, rami["WDATA"]))

    # PC MEMs: DATA = rq?0:S_NEXTPC ; WE = MAX(WB_pos&~HALT, rq)
    # Both DATA select and WE reset-term use rq -> consistent pair per MEM.
    wb_nh = _mux2(b, wb_pos, b.const(0), ha_out)   # wb_pos gated by ~halted
    pc_we = b.binary("MAX", wb_nh, rq)
    for i in range(9):
        m_id = pc_mem_refs[i][0]
        b.wire(_mux2(b, s_nextpc[i], b.const(-1), rq), (m_id, 0))
        b.wire(pc_we, (m_id, 1))

    # FLAG MEM: WE = MAX(FLAG_WE&WB, rq); DATA = rq?0:S_FLAG_DATA
    fl_we = b.binary("MAX", wb_and(s_fwe), rq)
    b.wire(_mux2(b, s_fdata, b.const(0), rq), (fl, 0))
    b.wire(fl_we, (fl, 1))
    # CARRY MEM
    ca_we = b.binary("MAX", wb_and(s_cwe), rq)
    b.wire(_mux2(b, s_cdata, b.const(0), rq), (ca, 0))
    b.wire(ca_we, (ca, 1))
    # HALT MEM: WE = MAX(HALT&WB, rq); DATA = rq?0:+1
    ha_we = b.binary("MAX", wb_and(s_halt), rq)
    b.wire(_mux2(b, b.const(1), b.const(0), rq), (ha, 0))
    b.wire(ha_we, (ha, 1))

    # PH MEM wiring
    b.wire(ph_data, (ph, 0))
    b.wire(we_ph, (ph, 1))

    # monitor outputs: R{v} pin <-> REGFILE MON{v+13}
    for k in range(27):
        b.wire((rf, rfo[f"MON{k}"]), b.out_ref(mon_pins[k]))

    return b.register()


# ---------------------------------------------------------------------------
# COBALT_SYS: COBALT core + external ROM, pre-wired. Drop-in CPU; the ROM
# subchip stays editable in-simulator.
# ---------------------------------------------------------------------------
def build_cobalt_sys(program):
    b = ChipBuilder("COBALT_SYS", colour=(0.15, 0.35, 0.75, 1.0))
    rst = b.add_input("RESET", 1)
    mode = b.add_input("MODE", 1)
    step = b.add_input("STEP", 1)

    # Keep the editor pins on a clean grid: status column on the far right,
    # monitor registers as 9 columns x 3 rows (R-13..R-5 / R-4..R4 / R5..R13).
    b.lock_output_positions = True
    pc9 = b.add_output("PC", 9, x=39.0, y=1.2)
    flags = b.add_output("FLAG", 1, x=39.0, y=0.6)
    carry = b.add_output("CARRY", 1, x=39.0, y=0.0)
    phase = b.add_output("PHASE", 1, x=39.0, y=-0.6)
    halted = b.add_output("HALTED", 1, x=39.0, y=-1.2)
    mon_pins = []
    for k in range(27):
        row, col = divmod(k, 9)
        mon_pins.append(b.add_output(f"R{k - 13}", 9,
                                     x=22.0 + col * 1.6,
                                     y=-row * 1.0))

    rom_data = [0] * 19683
    for addr, instr in program.items():
        rom_data[addr] = pack_trits(instr)
    rom = b.sub("ROM 19683x9", x=14, y=0, internal=rom_data, label="PROGRAM")
    rin, rout = _rom_pins()

    co = b.sub("COBALT", x=-10, y=0, label="COBALT")
    ci, co_ = chip_pin_ids("COBALT")

    b.wire(b.in_ref(rst), (co, ci["RESET"]))
    b.wire(b.in_ref(mode), (co, ci["MODE"]))
    b.wire(b.in_ref(step), (co, ci["STEP"]))
    b.wire((co, co_["PC"]), (rom, rin))
    b.wire((rom, rout), (co, ci["INSTR"]))

    b.wire((co, co_["PC"]), b.out_ref(pc9))
    b.wire((co, co_["FLAG"]), b.out_ref(flags))
    b.wire((co, co_["CARRY"]), b.out_ref(carry))
    b.wire((co, co_["PHASE"]), b.out_ref(phase))
    b.wire((co, co_["HALTED"]), b.out_ref(halted))
    for k in range(27):
        b.wire((co, co_[f"R{k - 13}"]), b.out_ref(mon_pins[k]))
    return b.register()


BUILDERS2 = [build_shift9, build_decode, build_alu, build_ctrl, build_exec,
             build_regfile, build_ram27]
