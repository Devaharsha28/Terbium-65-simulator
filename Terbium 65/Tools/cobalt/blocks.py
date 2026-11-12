"""Cobalt hardware blocks: build custom chip descriptions into REGISTRY.

Each builder creates a ChipBuilder, populates it, registers the chip, and
returns the chip name. Pin interface documented per builder.
"""

from chips import ChipBuilder, REGISTRY, nid, chip_pin_ids
from isa import value_trits, trits_value, NEG, ZERO, POS


# ---------------------------------------------------------------------------
# MUX2: out = SEL==+1 ? B : A        (A,B,SEL 1-trit -> OUT)
# ---------------------------------------------------------------------------
def build_mux2():
    b = ChipBuilder("MUX2", colour=(0.85,0.7,0.3,1.0))
    a = b.add_input("A", 1)
    bb = b.add_input("B", 1)
    sel = b.add_input("SEL", 1)
    out = b.add_output("OUT", 1)
    aref, bref, sref = b.in_ref(a), b.in_ref(bb), b.in_ref(sel)
    sb = b.unary("ISP", sref)          # +1 iff sel==+1
    nsb = b.unary("NOT", sb)           # +1 iff sel!=+1
    t1 = b.binary("MIN", bref, sb)     # sel? b : -1
    t2 = b.binary("MIN", aref, nsb)    # !sel? a : -1
    r = b.binary("MAX", t1, t2)
    b.wire(r, b.out_ref(out))
    return b.register()


# ---------------------------------------------------------------------------
# ADDER9: A9+B9 -> SUM9, CO    (verified vs isa.add9 semantics)
# cin = 0 constant.
# ---------------------------------------------------------------------------
def _fa(b, a, bb, cin, x, y):
    """one trit full adder; returns (sum_ref, carry_ref)."""
    s1 = b.binary("SUM", a, bb)
    s = b.binary("SUM", s1, cin)
    c1 = b.binary("CONS", a, bb)
    c2 = b.binary("CONS", s1, cin)
    c = b.binary("ANY", c1, c2)
    return s, c


def build_adder9():
    b = ChipBuilder("ADDER9", colour=(0.3,0.5,0.8,1.0))
    a9 = b.add_input("A", 9)
    b9 = b.add_input("B", 9)
    sum9 = b.add_output("SUM", 9)
    co = b.add_output("CO", 1)
    ta = b.split9(b.in_ref(a9))
    tb = b.split9(b.in_ref(b9))
    cin = b.const(0)
    carries = []
    sums = []
    c = cin
    for i in range(9):
        s, c = _fa(b, ta[i], tb[i], c, 0, 0)
        sums.append(s)
        carries.append(c)
    outbus = b.merge1to9(sums)
    b.wire(outbus, b.out_ref(sum9))
    b.wire(carries[8], b.out_ref(co))
    return b.register()


# ---------------------------------------------------------------------------
# SUB9: A9-B9 -> SUM9, CO   (= ADDER9(A, NOT(B)))
# ---------------------------------------------------------------------------
def build_sub9():
    b = ChipBuilder("SUB9", colour=(0.3,0.5,0.8,1.0))
    a9 = b.add_input("A", 9)
    b9 = b.add_input("B", 9)
    sum9 = b.add_output("SUM", 9)
    co = b.add_output("CO", 1)
    tb = b.split9(b.in_ref(b9))
    nb = [b.unary("NOT", t) for t in tb]
    nb9 = b.merge1to9(nb)
    ad = b.sub("ADDER9")
    ain, aout = chip_pin_ids("ADDER9")
    b.wire(b.in_ref(a9), (ad, ain["A"]))
    b.wire(nb9, (ad, ain["B"]))
    b.wire((ad, aout["SUM"]), b.out_ref(sum9))
    b.wire((ad, aout["CO"]), b.out_ref(co))
    return b.register()


# ---------------------------------------------------------------------------
# CMP9: A9 vs B9 lexicographic (MSB first) -> FL in {-1,0,+1}
# per trit: eq_b, gt_b, lt_b booleans (+1/-1)
#   eq_b = ISZ(SUM(a, NOT(b)))
#   gt_b = a>b : search-derived formula (verified exhaustively in test)
#   lt_b = gt_b(b,a)
# suffix AND of eq -> decision terms -> G=MAX gt-decisions, L=MAX lt-decisions
# FL = SUM(CLU(G), CLD(NOT(L)))
# ---------------------------------------------------------------------------

def _gtb(b, a, bb, x, y):
    """boolean +1 iff a>b (trit-wise)."""
    # gt = (a==1 & b!=1) | (a==0 & b==-1)
    pa = b.unary("ISP", a)              # +1 iff a==1
    za = b.unary("ISZ", a)              # +1 iff a==0
    pb = b.unary("ISP", bb)             # +1 iff b==1
    nb_ = b.unary("ISN", bb)            # +1 iff b==-1
    npb = b.unary("NOT", pb)            # +1 iff b!=1
    t1 = b.binary("MIN", pa, npb)       # a==1 & b!=1
    t2 = b.binary("MIN", za, nb_)       # a==0 & b==-1
    return b.binary("MAX", t1, t2)


def build_cmp9():
    b = ChipBuilder("CMP9", colour=(0.3,0.5,0.8,1.0))
    a9 = b.add_input("A", 9)
    b9 = b.add_input("B", 9)
    fl = b.add_output("FL", 1)
    ta = b.split9(b.in_ref(a9))
    tb = b.split9(b.in_ref(b9))
    ntr = [b.unary("NOT", t) for t in tb]

    eq = []   # eq_b per trit (index 0=LSB)
    gt = []
    lt = []
    for i in range(9):
        s = b.binary("SUM", ta[i], ntr[i])
        eq.append(b.unary("ISZ", s))
        gt.append(_gtb(b, ta[i], tb[i], 0, 0))
        lt.append(_gtb(b, tb[i], ta[i], 0, 0))

    # suffix-eq: suf[i] = eq[i] AND eq[i+1] AND ... AND eq[8]  (i from 8 down)
    suf = [None] * 9
    suf[8] = eq[8]
    for i in range(7, -1, -1):
        suf[i] = b.binary("MIN", eq[i], suf[i + 1])

    # decision at trit i requires all ABOVE equal: prefix_eq_i = suf[i+1]
    g_terms = []
    l_terms = []
    for i in range(9):
        above = suf[i + 1] if i < 8 else b.const(1)
        g_terms.append(b.binary("MIN", gt[i], above))
        l_terms.append(b.binary("MIN", lt[i], above))
    G = g_terms[0]
    for t in g_terms[1:]:
        G = b.binary("MAX", G, t)
    L = l_terms[0]
    for t in l_terms[1:]:
        L = b.binary("MAX", L, t)
    gpos = b.unary("CLU", G)             # +1 if some gt decides
    nL = b.unary("NOT", L)
    lneg = b.unary("CLD", nL)            # -1 if some lt decides
    r = b.binary("SUM", gpos, lneg)
    b.wire(r, b.out_ref(fl))
    return b.register()


# ---------------------------------------------------------------------------
# Trit-wise 9-trit ops: MIN9 MAX9 MUL9 CONS9 ANY9 IS9
# in A9,B9 -> OUT9
# ---------------------------------------------------------------------------
def _build_tw9(name, gate):
    b = ChipBuilder(name)
    a9 = b.add_input("A", 9)
    b9 = b.add_input("B", 9)
    o9 = b.add_output("OUT", 9)
    ta = b.split9(b.in_ref(a9))
    tb = b.split9(b.in_ref(b9))
    outs = [b.binary(gate, ta[i], tb[i]) for i in range(9)]
    bus = b.merge1to9(outs)
    b.wire(bus, b.out_ref(o9))
    return b.register()


def build_min9(): return _build_tw9("MIN9", "MIN")
def build_max9(): return _build_tw9("MAX9", "MAX")
def build_mul9(): return _build_tw9("MUL9", "MUL")
def build_cons9(): return _build_tw9("CONS9", "CONS")
def build_any9(): return _build_tw9("ANY9", "ANY")
def build_is9(): return _build_tw9("IS9", "IS9TRIT")  # placeholder, fixed below


# IS trit-wise = +1 iff equal else -1 = ISZ(SUM(a, NOT(b)))
def build_is9_real():
    b = ChipBuilder("IS9", colour=(0.3,0.5,0.8,1.0))
    a9 = b.add_input("A", 9)
    b9 = b.add_input("B", 9)
    o9 = b.add_output("OUT", 9)
    ta = b.split9(b.in_ref(a9))
    tb = b.split9(b.in_ref(b9))
    outs = []
    for i in range(9):
        nb = b.unary("NOT", tb[i])
        s = b.binary("SUM", ta[i], nb)
        outs.append(b.unary("ISZ", s))
    bus = b.merge1to9(outs)
    b.wire(bus, b.out_ref(o9))
    return b.register()


# ---------------------------------------------------------------------------
# NOT9: in9 -> out9 (9 NOT gates)
# ---------------------------------------------------------------------------
def build_not9():
    b = ChipBuilder("NOT9", colour=(0.3,0.5,0.8,1.0))
    i9 = b.add_input("IN", 9)
    o9 = b.add_output("OUT", 9)
    ti = b.split9(b.in_ref(i9))
    outs = [b.unary("NOT", t) for t in ti]
    bus = b.merge1to9(outs)
    b.wire(bus, b.out_ref(o9))
    return b.register()


BUILDERS = [
    build_mux2, build_adder9, build_sub9, build_cmp9,
    build_min9, build_max9, build_mul9, build_cons9, build_any9,
    build_not9, build_is9_real,
]
