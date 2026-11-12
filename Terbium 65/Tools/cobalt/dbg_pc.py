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

sim.set_input(iid("RESET"), [1]); sim.set_input(iid("MODE"), [0]); sim.set_input(iid("STEP"), [0])
for f in range(3):
    sim.step()
    print("rst frame", f, "PH", tr1("PHASE"), "PC", isa.trits_value(tr9("PC")), "HALT", tr1("HALTED"))
sim.set_input(iid("RESET"), [0])
for f in range(45):
    sim.step()
    pc = isa.trits_value(tr9("PC"))
    ph = tr1("PHASE")
    if f < 8 or pc != 0 or ph != -1:
        print("f%d PH=%s PC=%s HALT=%s INSTR=%s" % (f, ph, pc, tr1("HALTED"), tr9("INSTR")))
