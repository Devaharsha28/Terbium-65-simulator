"""Manual-mode stepping test with proper settle waits.

Phases: PHASE==-1 -> EXEC (stage captures), PHASE==+1 -> WB (commit).
Each STEP press attempts one PH toggle (~50% success due to MEM feedback
race), so we press until PHASE actually changes, then let the cone settle.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa, csim

PROJ = os.path.join("..", "..", "TestData", "Projects", "Cobalt")
COBALT = None


def pid(desc, name, key):
    for p in desc[key]:
        if p["Name"] == name:
            return p["ID"]
    raise KeyError(name)


def read(sim, desc, name, n):
    st = sim.get_output_state(pid(desc, name, "OutputPins"))
    return [csim.GetTritAtIndex(st, i) for i in range(n)]


def snapshot(sim, cobalt):
    return {
        "pc": isa.trits_value(read(sim, cobalt, "PC", 9)),
        "regs": {k: isa.trits_value(read(sim, cobalt, f"R{k}", 9))
                 for k in range(-4, 5)},
        "flag": read(sim, cobalt, "FLAG", 1)[0],
        "carry": read(sim, cobalt, "CARRY", 1)[0],
        "halted": read(sim, cobalt, "HALTED", 1)[0],
        "phase": read(sim, cobalt, "PHASE", 1)[0],
    }


def phase(sim, cobalt):
    return read(sim, cobalt, "PHASE", 1)[0]


def frames(sim, n):
    for _ in range(n):
        sim.step()


def press(sim, cobalt, hold=4, release=4):
    sim.set_input(pid(cobalt, "STEP", "InputPins"), [1])
    frames(sim, hold)
    sim.set_input(pid(cobalt, "STEP", "InputPins"), [0])
    frames(sim, release)


def wait_phase(sim, cobalt, want, max_presses=40):
    """Press STEP until PHASE == want."""
    for _ in range(max_presses):
        if phase(sim, cobalt) == want:
            return True
        press(sim, cobalt)
    return phase(sim, cobalt) == want


def main():
    global COBALT
    lib = csim.load_library(os.path.join(PROJ, "Chips"))
    COBALT = json.load(open(os.path.join(PROJ, "Chips", "COBALT_SYS.json")))
    cobalt = COBALT
    sim = csim.Sim(lib, cobalt)

    def iid(n): return pid(cobalt, n, "InputPins")
    sim.set_input(iid("RESET"), [1])
    sim.set_input(iid("MODE"), [0])
    sim.set_input(iid("STEP"), [0])
    frames(sim, 3)
    sim.set_input(iid("RESET"), [0])
    frames(sim, 3)

    # ensure EXEC phase and let the whole cone settle
    wait_phase(sim, cobalt, -1)
    frames(sim, 40)

    boundaries = []
    t0 = time.time()
    presses = 0
    for _ in range(15):
        # we should be in EXEC (-1); settle already done -> go WB
        if not wait_phase(sim, cobalt, 1):
            print("could not reach WB"); break
        presses += 1
        frames(sim, 15)          # WB commits (idempotent)
        s = snapshot(sim, cobalt)
        boundaries.append(s)
        if s["halted"] == 1:
            break
        # go back to EXEC and settle
        if not wait_phase(sim, cobalt, -1):
            print("could not reach EXEC"); break
        presses += 1
        frames(sim, 40)          # EXEC settle before next capture

    print(f"{len(boundaries)} instructions, {presses} presses, "
          f"{time.time()-t0:.1f}s")
    for i, s in enumerate(boundaries):
        nz = {k: v for k, v in s["regs"].items() if v != 0}
        print(f"  instr{i}: PC={s['pc']} flag={s['flag']} "
              f"carry={s['carry']} halt={s['halted']} regs={nz}")


if __name__ == "__main__":
    main()
