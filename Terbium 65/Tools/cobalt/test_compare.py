"""Compare COBALT hardware (csim, manual stepping) against isa.Machine.

For each committed instruction, compare PC, FLAG, CARRY, HALTED and the nine
active registers (MON outputs) against the emulator state.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa, csim
from gen_cobalt import BUBBLE_ASM
from test_manual import (pid, read, snapshot, phase, frames, press,
                         wait_phase, PROJ, COBALT)

def emu_snapshot(m):
    return {
        "pc": m.pc,
        "flag": m.flag,
        "carry": m.carry,
        "halted": 1 if m.halted else 0,
        "regs": {v: isa.trits_value(m.regs[v + 13]) for v in range(-4, 5)},
    }


def hw_snapshot(sim, cobalt):
    s = snapshot(sim, cobalt)
    return {"pc": s["pc"], "flag": s["flag"], "carry": s["carry"],
            "halted": s["halted"], "regs": s["regs"]}


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
    wait_phase(sim, cobalt, -1)
    frames(sim, 40)

    prog, _ = isa.assemble_program(BUBBLE_ASM)
    mach = isa.Machine(prog)

    hw_states = []
    emu_states = []
    t0 = time.time()
    for _ in range(15):
        if not wait_phase(sim, cobalt, 1):
            print("no WB"); break
        frames(sim, 15)
        hw_states.append(hw_snapshot(sim, cobalt))
        # emulator: step once per hardware instruction
        mach.step()
        emu_states.append(emu_snapshot(mach))
        if hw_states[-1]["halted"] == 1:
            break
        if not wait_phase(sim, cobalt, -1):
            print("no EXEC"); break
        frames(sim, 40)

    print(f"{len(hw_states)} hw instrs vs {len(emu_states)} emu steps, "
          f"{time.time()-t0:.1f}s")
    ok = True
    for i, (h, e) in enumerate(zip(hw_states, emu_states)):
        # hardware PC = emu index - 9841; after halt hw holds, emu pc+1
        epc = e["pc"] - 9841
        match = (h["flag"] == e["flag"] and h["carry"] == e["carry"]
                 and h["halted"] == e["halted"]
                 and all(h["regs"][k] == e["regs"][k] for k in range(-4, 5))
                 and (h["pc"] == epc or (e["halted"] and h["pc"] == epc - 1)))
        status = "OK " if match else "FAIL"
        if not match:
            ok = False
        print(f"{status} instr{i}: hw pc={h['pc']} emu pc={epc} "
              f"flag {h['flag']}/{e['flag']} carry {h['carry']}/{e['carry']} "
              f"halt {h['halted']}/{e['halted']}")
        if not match:
            for k in range(-4, 5):
                if h["regs"][k] != e["regs"][k]:
                    print(f"      reg r{k}: hw={h['regs'][k]} emu={e['regs'][k]}")
    print("ALL MATCH" if ok and len(hw_states) == len(emu_states) else "MISMATCH")


if __name__ == "__main__":
    main()
