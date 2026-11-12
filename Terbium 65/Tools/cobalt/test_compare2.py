"""Extended ISA coverage test: jumps, shifts, flags, RAM, more ALU ops."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa, csim
from test_manual import (pid, read, snapshot, phase, frames, press,
                         wait_phase)

PROJ = os.path.join("..", "..", "TestData", "Projects", "Cobalt2")

DEMO2 = """
start:
        LDI.L r1, 1
        LDI.M r1, 0
        LDI.H r1, 0      ; r1 = 1
        LDI.L r2, 2
        LDI.M r2, 0
        LDI.H r2, 0      ; r2 = 2
        SHL r1, r2       ; r1 = 4
        MOV.GA r1, r5    ; r5 = 4
        MOV.AG r4, r5    ; r4 = 4
        SHR r4, r2       ; r4 = 1
        RL  r4, r2       ; r4 = rotate-left(1,2)
        RR  r4, r2       ; r4 = rotate-right
        ADD r4, r2       ; r4 += 2
        SUB r4, r1       ; r4 -= r1(=4)
        CMP r4, r2       ; flag = cmp(r4, 2)
        JG  big          ; if r4 > 2 -> big
        LDI.L r4, 0      ; r4 = 0 (not taken path)
big:    IS  r4, r2       ; r4 = (r4==2)?1:-1 per trit
        ANY r4, r2       ; r4 = any-sum clamp
        CONS r4, r2      ; r4 = cons
        MIN r4, r1       ; r4 = min
        MAX r4, r1       ; r4 = max
        MUL r4, r2       ; r4 *= 2
        ; RAM test: store r2 at addr r3=0, load back
        LDI.L r3, 0
        LDI.M r3, 0
        LDI.H r3, 0      ; r3 = 0
        MOV.AG r4, r5    ; save r4 -> r5? no: r4=r5... use STR
        STR r3, r2       ; mem[r3] = r2   (A=addr r3, X=data r2)
        LDA r3, r4       ; r4 = mem[r3]
        ; flag/carry jump test
        CMP r4, r1       ; flag
        JE  eqpath       ; if equal
eqpath: NOP
        HALT
"""


def emu_snapshot(m):
    return {
        "pc": m.pc, "flag": m.flag, "carry": m.carry,
        "halted": 1 if m.halted else 0,
        "regs": {v: isa.trits_value(m.regs[v + 13]) for v in range(-4, 5)},
    }


def hw_snapshot(sim, cobalt):
    s = snapshot(sim, cobalt)
    return {"pc": s["pc"], "flag": s["flag"], "carry": s["carry"],
            "halted": s["halted"], "regs": s["regs"]}


def main():
    prog, labels = isa.assemble_program(DEMO2)
    print("program:", len(prog), "instrs, labels:", labels)
    lib = csim.load_library(os.path.join(PROJ, "Chips"))
    cobalt = json.load(open(os.path.join(PROJ, "Chips", "COBALT_SYS.json")))
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

    mach = isa.Machine(prog)
    hw_states, emu_states = [], []
    t0 = time.time()
    for _ in range(len(prog) + 5):
        if not wait_phase(sim, cobalt, 1):
            print("no WB"); break
        frames(sim, 15)
        hw_states.append(hw_snapshot(sim, cobalt))
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
        epc = e["pc"] - 9841
        match = (h["flag"] == e["flag"] and h["carry"] == e["carry"]
                 and h["halted"] == e["halted"]
                 and all(h["regs"][k] == e["regs"][k] for k in range(-4, 5))
                 and (h["pc"] == epc or (e["halted"] and h["pc"] == epc - 1)))
        if not match:
            ok = False
            print(f"FAIL instr{i}: hw pc={h['pc']} emu pc={epc} "
                  f"flag {h['flag']}/{e['flag']} carry {h['carry']}/{e['carry']} "
                  f"halt {h['halted']}/{e['halted']}")
            for k in range(-4, 5):
                if h["regs"][k] != e["regs"][k]:
                    print(f"      r{k}: hw={h['regs'][k]} emu={e['regs'][k]}")
        else:
            print(f"OK  instr{i}: pc={h['pc']} regs={ {k:v for k,v in h['regs'].items() if v} }")
    print("ALL MATCH" if ok else "MISMATCH")


if __name__ == "__main__":
    main()
