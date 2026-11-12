"""Verify hardware blocks against isa.py semantics using csim."""
import sys, os, random, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa, csim, chips, blocks


def build_lib():
    chips.REGISTRY.clear()
    for b in blocks.BUILDERS:
        b()
    return chips.REGISTRY


def mk_sim(lib, chip_name):
    desc = lib[chip_name.lower()]
    return csim.Sim(lib, desc)


def drive(sim, pin_name, trits):
    # find boundary input pin id by name
    for p in sim.root.InputPins:
        if p.Name == pin_name if hasattr(p, 'Name') else False:
            pass
    # SimPin has no Name; find via desc
    for pd in sim.root_desc.get("InputPins", []) if hasattr(sim, 'root_desc') else []:
        pass


def pin_id(desc, pins_key, name):
    for p in desc[pins_key]:
        if p["Name"] == name:
            return p["ID"]
    raise KeyError(name)


def out_trits(sim, desc, name, n=9):
    pid = pin_id(desc, "OutputPins", name)
    st = sim.get_output_state(pid)
    return [csim.GetTritAtIndex(st, i) for i in range(n)]


def in_trits(desc, name):
    for p in desc["InputPins"]:
        if p["Name"] == name:
            return p["TritCount"], p["ID"]
    raise KeyError(name)


def set_pin(sim, desc, name, trits):
    _, pid = in_trits(desc, name)
    sim.set_input(pid, trits)


def settle(sim, frames=3):
    for _ in range(frames):
        sim.step()


def test_mux2(lib):
    name = "MUX2"
    desc = lib[name.lower()]
    sim = mk_sim(lib, name)
    for a in isa.TRITS:
        for bb in isa.TRITS:
            for s in isa.TRITS:
                set_pin(sim, desc, "A", [a])
                set_pin(sim, desc, "B", [bb])
                set_pin(sim, desc, "SEL", [s])
                settle(sim)
                got = out_trits(sim, desc, "OUT", 1)[0]
                exp = bb if s == 1 else a
                assert got == exp, (a, bb, s, got, exp)
    print("MUX2 OK (27)")


def test_adder9(lib):
    name = "ADDER9"
    desc = lib[name.lower()]
    sim = mk_sim(lib, name)
    rng = random.Random(7)
    cases = [(0, 0)]
    for _ in range(3000):
        va = rng.randint(-9841, 9841)
        vb = rng.randint(-9841, 9841)
        cases.append((va, vb))
    # edge cases
    for va in (-9841, -1, 0, 1, 9841):
        for vb in (-9841, -1, 0, 1, 9841):
            cases.append((va, vb))
    for va, vb in cases:
        a = isa.value_trits(va, 9)
        b = isa.value_trits(vb, 9)
        set_pin(sim, desc, "A", a)
        set_pin(sim, desc, "B", b)
        settle(sim)
        got = out_trits(sim, desc, "SUM", 9)
        co = out_trits(sim, desc, "CO", 1)[0]
        exp_r, exp_c = isa.add9(a, b)
        assert got == exp_r, (va, vb, got, exp_r)
        assert co == exp_c, (va, vb, co, exp_c)
    print(f"ADDER9 OK ({len(cases)} cases)")


def test_sub9(lib):
    name = "SUB9"
    desc = lib[name.lower()]
    sim = mk_sim(lib, name)
    rng = random.Random(8)
    for _ in range(3000):
        va = rng.randint(-9841, 9841)
        vb = rng.randint(-9841, 9841)
        a = isa.value_trits(va, 9)
        b = isa.value_trits(vb, 9)
        set_pin(sim, desc, "A", a)
        set_pin(sim, desc, "B", b)
        settle(sim)
        got = out_trits(sim, desc, "SUM", 9)
        co = out_trits(sim, desc, "CO", 1)[0]
        exp_r, exp_c = isa.sub9(a, b)
        assert got == exp_r, (va, vb)
        assert co == exp_c, (va, vb, co, exp_c)
    print("SUB9 OK")


def test_cmp9(lib):
    name = "CMP9"
    desc = lib[name.lower()]
    sim = mk_sim(lib, name)
    rng = random.Random(9)
    # exhaustive small + random
    cases = []
    for va in range(-20, 21):
        for vb in range(-20, 21):
            cases.append((va, vb))
    for _ in range(3000):
        cases.append((rng.randint(-9841, 9841), rng.randint(-9841, 9841)))
    # also random trit patterns (not just canonical values)
    for _ in range(2000):
        a = [rng.choice(isa.TRITS) for _ in range(9)]
        b = [rng.choice(isa.TRITS) for _ in range(9)]
        set_pin(sim, desc, "A", a)
        set_pin(sim, desc, "B", b)
        settle(sim)
        got = out_trits(sim, desc, "FL", 1)[0]
        exp = isa.cmp9(a, b)
        assert got == exp, (a, b, got, exp)
    for va, vb in cases:
        a = isa.value_trits(va, 9)
        b = isa.value_trits(vb, 9)
        set_pin(sim, desc, "A", a)
        set_pin(sim, desc, "B", b)
        settle(sim)
        got = out_trits(sim, desc, "FL", 1)[0]
        exp = isa.cmp9(a, b)
        assert got == exp, (va, vb, got, exp)
    print(f"CMP9 OK ({len(cases)+2000} cases)")


def test_tw9(lib, name, gate):
    desc = lib[name.lower()]
    sim = mk_sim(lib, name)
    rng = random.Random(11)
    for _ in range(200):
        a = [rng.choice(isa.TRITS) for _ in range(9)]
        b = [rng.choice(isa.TRITS) for _ in range(9)]
        set_pin(sim, desc, "A", a)
        set_pin(sim, desc, "B", b)
        settle(sim)
        got = out_trits(sim, desc, "OUT", 9)
        if name == "IS9":
            exp = [1 if a[i] == b[i] else -1 for i in range(9)]
        else:
            ct = {"MIN": csim.CT.Min, "MAX": csim.CT.Max, "MUL": csim.CT.Mul,
                  "CONS": csim.CT.Cons, "ANY": csim.CT.Any}[gate]
            exp = [csim.EvaluateBinary(ct, a[i], b[i]) for i in range(9)]
        assert got == exp, (name, a, b, got, exp)
    print(f"{name} OK")


def test_not9(lib):
    desc = lib["not9"]
    sim = mk_sim(lib, "NOT9")
    rng = random.Random(12)
    for _ in range(100):
        a = [rng.choice(isa.TRITS) for _ in range(9)]
        set_pin(sim, desc, "IN", a)
        settle(sim)
        got = out_trits(sim, desc, "OUT", 9)
        exp = [-t for t in a]
        assert got == exp
    print("NOT9 OK")


def main():
    lib = build_lib()
    print("chips:", {k: (len(v["SubChips"]), len(v["Wires"])) for k, v in lib.items()})
    test_mux2(lib)
    test_adder9(lib)
    test_sub9(lib)
    test_cmp9(lib)
    for nm, gt in [("MIN9","MIN"),("MAX9","MAX"),("MUL9","MUL"),("CONS9","CONS"),("ANY9","ANY")]:
        test_tw9(lib, nm, gt)
    test_tw9(lib, "IS9", "IS")
    test_not9(lib)
    print("ALL BLOCK TESTS PASSED")


if __name__ == "__main__":
    main()
