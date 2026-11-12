import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa, csim

PROJ = os.path.join("..", "..", "TestData", "Projects", "Cobalt")
lib = csim.load_library(os.path.join(PROJ, "Chips"))
cobalt = json.load(open(os.path.join(PROJ, "Chips", "COBALT.json")))
sim = csim.Sim(lib, cobalt)


def pid(n, k):
    return [p["ID"] for p in cobalt[k] if p["Name"] == n][0]


def tr1(n):
    st = sim.get_output_state(pid(n, "OutputPins"))
    return csim.GetTritAtIndex(st, 0)


def tr9(n):
    st = sim.get_output_state(pid(n, "OutputPins"))
    return [csim.GetTritAtIndex(st, i) for i in range(9)]


iid = lambda n: pid(n, "InputPins")


def frames(n):
    for _ in range(n):
        sim.step()


def press(h=4, r=4):
    sim.set_input(iid("STEP"), [1]); frames(h)
    sim.set_input(iid("STEP"), [0]); frames(r)


sim.set_input(iid("RESET"), [1]); sim.set_input(iid("MODE"), [0]); sim.set_input(iid("STEP"), [0])
frames(3); sim.set_input(iid("RESET"), [0]); frames(3)
print("start PHASE", tr1("PHASE"), "PC", isa.trits_value(tr9("PC")))
frames(40)
print("settled PHASE", tr1("PHASE"), "PC", isa.trits_value(tr9("PC")))
for i in range(14):
    press()
    print("press%d: PHASE=%s PC=%s HALT=%s INSTR=%s" % (
        i, tr1("PHASE"), isa.trits_value(tr9("PC")), tr1("HALTED"), tr9("INSTR")))
