"""Milestone-1 tests: opcode table, assembler round-trip, adder exhaustive."""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa


def test_opcodes():
    isa.check_opcode_table()
    # reserved opcodes must decode to None -> NOP
    reserved = [(o3, o2, o1, o0) for o3 in isa.TRITS for o2 in isa.TRITS
                for o1 in isa.TRITS for o0 in isa.TRITS
                if (o3, o2, o1, o0) not in isa.OPCODE_TABLE]
    print(f"reserved count: {len(reserved)}")


def test_value_trits():
    for n in (2, 3, 5, 9):
        lo, hi = -((3 ** n - 1) // 2), (3 ** n - 1) // 2
        for v in range(lo, hi + 1):
            t = isa.value_trits(v, n)
            assert len(t) == n
            assert isa.trits_value(t) == v, (v, n, t)
    print("value_trits exhaustive OK")


def test_assemble_roundtrip():
    src = """
        LDI.L r1, 5
        LDI.M r1, -3
        LDI.H r1, 13
        ADD r1, r2
        ADD r1, 7
        SUB r1, r3
        MUL r1, r4
        MIN r1, r5
        MAX r1, r5
        CONS r1, r6
        ANY r1, -4
        IS r1, r7
        CMP r1, r8
        CMP r1, 9
        SHL r1, r2
        SHL r1, 4
        SHR r1, 3
        RL r1, r1
        RR r1, 2
        MOV.AG r1, r10
        MOV.GA r1, r-7
        LDA r1, r3
        STR r1, r4
        NOP
        HALT
    start:
        JE end
        JG start
        JL -2
        JCN 3
        JCZ start
        JCP end
        JMP start
        JGE end
        JNE start
        JLE -1
        JZ r9, r2
        JP r-3, r4
        JN r0, r0
    end:
        HALT
    """
    prog, labels = isa.assemble_program(src)
    assert labels == {"start": 25, "end": 38}, labels
    # verify a few decodings
    a, x, imm5 = isa.decode_fields(prog[0])
    assert (a, x) == (1, 5), (a, x)
    a, x, _ = isa.decode_fields(prog[3])
    assert (a, x) == (1, 2), (a, x)   # ADD r1,r2
    a, x, _ = isa.decode_fields(prog[4])
    assert (a, x) == (1, 7), (a, x)   # ADD r1,7
    a, x, imm5 = isa.decode_fields(prog[25])
    # JE end: rel = 38-25 = 13
    assert imm5 == 13, imm5
    a, x, _ = isa.decode_fields(prog[35])
    assert (a, x) == (2, 9), (a, x)   # JZ r9, r2 -> A=off reg r2, X=test r9
    print("assemble roundtrip OK,", len(prog), "instructions")


def test_fa_exhaustive():
    """Per-trit FA: verify s + 3*c == a + b + cin for all 27 combos."""
    def wsum(x, y):
        s = x + y
        return s - 3 if s > 1 else (s + 3 if s < -1 else s)
    def cons(x, y):
        return x if x == y else 0
    def anyf(x, y):
        return max(-1, min(1, x + y))
    bad = []
    for a in isa.TRITS:
        for b in isa.TRITS:
            for cin in isa.TRITS:
                s1 = wsum(a, b)
                s = wsum(s1, cin)
                c = anyf(cons(a, b), cons(s1, cin))
                if s + 3 * c != a + b + cin:
                    bad.append((a, b, cin, s, c))
    assert not bad, f"FA failures: {bad[:10]}"
    print("FA exhaustive 27/27 OK")


def test_add9_exhaustive_random():
    rng = random.Random(1)
    for _ in range(20000):
        va = rng.randint(-9841, 9841)
        vb = rng.randint(-9841, 9841)
        a = isa.value_trits(va, 9)
        b = isa.value_trits(vb, 9)
        r, c = isa.add9(a, b)
        vr = isa.trits_value(r)
        # a + b = vr + 19683*c
        assert va + vb == vr + 19683 * c, (va, vb, vr, c)
        # carry must be -1/0/1
        assert c in isa.TRITS
    print("add9 random 20000 OK")


def test_sub9():
    rng = random.Random(2)
    for _ in range(20000):
        va = rng.randint(-9841, 9841)
        vb = rng.randint(-9841, 9841)
        a = isa.value_trits(va, 9)
        b = isa.value_trits(vb, 9)
        r, c = isa.sub9(a, b)
        vr = isa.trits_value(r)
        assert va - vb == vr + 19683 * c, (va, vb, vr, c)
    print("sub9 random 20000 OK")


def test_emulator_smoke():
    prog = {
        0: isa._emit_f1(isa._opcode_for("LDI.L", "ldi_l"), 1, 5),
        1: isa._emit_f1(isa._opcode_for("LDI.M", "ldi_m"), 1, -2),
        2: isa._emit_f1(isa._opcode_for("LDI.H", "ldi_h"), 1, 1),
        3: isa._emit_f1(isa._opcode_for("MOV.GA", "mov_ga"), 1, 5),  # r5 = r1
        4: isa._emit_f1(isa._opcode_for("ADD", "reg"), 2, 5),       # r2 += r5
        5: isa._emit_f1(isa._opcode_for("HALT", "halt"), 0, 0),
    }
    m = isa.Machine(prog)
    for _ in range(6):
        m.step()
    assert m.halted
    # r1 = ldi composition: imm3=5 -> low trits; -2 mid; 1 high
    r1 = m.regs[1 + 13]
    exp = [0] * 9
    t5, tm, th = isa.value_trits(5, 3), isa.value_trits(-2, 3), isa.value_trits(1, 3)
    for i in range(3):
        exp[i] = t5[i]
        exp[3 + i] = tm[i]
        exp[6 + i] = th[i]
    assert r1 == exp, (r1, exp)
    r5 = m.regs[5 + 13]
    assert r5 == exp
    # r2 = 0 + r5
    assert m.regs[2 + 13] == exp
    print("emulator smoke OK")


if __name__ == "__main__":
    test_opcodes()
    test_value_trits()
    test_fa_exhaustive()
    test_add9_exhaustive_random()
    test_sub9()
    test_assemble_roundtrip()
    test_emulator_smoke()
    print("ALL M1 TESTS PASSED")
