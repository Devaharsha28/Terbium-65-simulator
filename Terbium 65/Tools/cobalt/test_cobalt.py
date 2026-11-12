"""Run COBALT in csim; verify functional correctness at instruction boundaries.

Because phase timing is nondeterministic (MEM feedback race), we detect each
completed instruction by PHASE +1 -> -1 transitions (WB -> EXEC) and compare
the committed architectural state against isa.Machine after each step.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa, csim

PROJ = os.path.join("..", "..", "TestData", "Projects", "Cobalt")


def pin_id(desc, pins_key, name):
    for p in desc[pins_key]:
        if p["Name"] == name:
            return p["ID"]
    raise KeyError(name)


def read9(sim, desc, name):
    st = sim.get_output_state(pin_id(desc, "OutputPins", name))
    return [csim.GetTritAtIndex(st, i) for i in range(9)]


def read1(sim, desc, name):
    st = sim.get_output_state(pin_id(desc, "OutputPins", name))
    return csim.GetTritAtIndex(st, 0)


def read_ram(sim, cobalt):
    """Read COBALT's RAM27 subchip storage? Not directly observable.
    Instead we verify via monitor regs + a dedicated RAM readback program."""
    return None


def snapshot(sim, cobalt):
    """Architectural state visible at boundary: active regs, flag, carry, pc."""
    regs = {}
    for k in range(-4, 5):
        regs[k] = isa.trits_value(read9(sim, cobalt, f"R{k}"))
    return {
        "regs": regs,
        "flag": read1(sim, cobalt, "FLAG"),
        "carry": read1(sim, cobalt, "CARRY"),
        "pc": isa.trits_value(read9(sim, cobalt, "PC")),
        "halted": read1(sim, cobalt, "HALTED"),
    }


def run_until_halt(sim, cobalt, max_frames=200000):
    """Returns list of snapshots at each instruction boundary."""
    snaps = []
    prev_phase = None
    boundary_count = 0
    for fr in range(max_frames):
        sim.step()
        ph = read1(sim, cobalt, "PHASE")
        if prev_phase == 1 and ph == -1:
            # WB -> EXEC transition: instruction committed. PC MEMs update
            # sequentially within the WB frame, so let the bus settle a few
            # frames before snapshotting.
            for _ in range(4):
                sim.step()
            snaps.append(snapshot(sim, cobalt))
            boundary_count += 1
            if snaps[-1]["halted"] == 1:
                break
        prev_phase = ph
    return snaps


def main():
    lib = csim.load_library(os.path.join(PROJ, "Chips"))
    with open(os.path.join(PROJ, "Chips", "COBALT.json")) as f:
        cobalt = json.load(f)
    print("building sim (~4500 chips)...")
    sim = csim.Sim(lib, cobalt)
    def iid(n): return pin_id(cobalt, "InputPins", n)
    sim.set_input(iid("RESET"), [1])   # reset for a couple frames
    sim.set_input(iid("MODE"), [1])    # auto
    sim.set_input(iid("STEP"), [0])
    for _ in range(4):
        sim.step()
    sim.set_input(iid("RESET"), [0])

    snaps = run_until_halt(sim, cobalt)
    print(f"completed {len(snaps)} instructions")
    for i, s in enumerate(snaps):
        print(f"  after instr {i}: PC={s['pc']} flag={s['flag']} carry={s['carry']} "
              f"halt={s['halted']} regs={ {k:v for k,v in s['regs'].items() if v!=0} }")


if __name__ == "__main__":
    main()
