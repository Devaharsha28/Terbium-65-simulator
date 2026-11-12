"""Run the Bubble Sort program baked into the Cobalt project's ROM.

Uses csim to execute the generated COBALT_SYS chip JSON, then reads the
RAM27 cells that the program sorts (addresses -13..-9 = cells 0..4).
Also runs isa.Machine as a reference and compares the final RAM contents.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isa, csim
from gen_cobalt import BUBBLE_ASM
from test_manual import pid, read, phase, frames, press, wait_phase

PROJ = os.path.join("..", "..", "TestData", "Projects", "Cobalt")


def find_by_id(chip, wanted):
    if chip.ID == wanted:
        return chip
    for s in chip.SubChips:
        found = find_by_id(s, wanted)
        if found is not None:
            return found
    return None


def ram_layout():
    ram_desc = json.load(open(os.path.join(PROJ, "Chips", "RAM27.json")))
    cobalt_desc = json.load(open(os.path.join(PROJ, "Chips", "COBALT.json")))
    ram27_id = next(sd["ID"] for sd in cobalt_desc["SubChips"]
                    if sd["Name"] == "RAM27")
    mem_ids = {}
    for sd in ram_desc["SubChips"]:
        label = sd.get("Label") or ""
        if label.startswith("RAM") and "." in label:
            v_s, i_s = label[3:].split(".")
            mem_ids[(int(v_s), int(i_s))] = sd["ID"]
    return ram27_id, mem_ids


def read_ram_cell(ram_chip, mem_ids, mem_by_id, addr):
    trits = []
    for i in range(9):
        mem = mem_by_id[mem_ids[(addr, i)]]
        trits.append(csim.GetTritValue(mem.InternalState[0]))
    return isa.trits_value(trits)


def emu_result():
    prog, _ = isa.assemble_program(BUBBLE_ASM)
    mach = isa.Machine(prog)
    while not mach.halted and mach.steps < 10000:
        mach.step()
    return [isa.trits_value(mach.ram[i]) for i in range(5)], mach.steps


def main():
    lib = csim.load_library(os.path.join(PROJ, "Chips"))
    cobalt = json.load(open(os.path.join(PROJ, "Chips", "COBALT_SYS.json")))
    sim = csim.Sim(lib, cobalt)

    def iid(n):
        return pid(cobalt, n, "InputPins")

    sim.set_input(iid("RESET"), [1])
    sim.set_input(iid("MODE"), [0])
    sim.set_input(iid("STEP"), [0])
    frames(sim, 3)
    sim.set_input(iid("RESET"), [0])
    frames(sim, 3)
    wait_phase(sim, cobalt, -1)
    frames(sim, 40)

    instrs = 0
    for _ in range(1000):
        if not wait_phase(sim, cobalt, 1):
            print("could not reach WB phase")
            break
        frames(sim, 15)
        instrs += 1
        if read(sim, cobalt, "HALTED", 1)[0] == 1:
            break
        if not wait_phase(sim, cobalt, -1):
            print("could not reach EXEC phase")
            break
        frames(sim, 40)

    ram27_id, mem_ids = ram_layout()
    ram_chip = find_by_id(sim.root, ram27_id)
    mem_by_id = {s.ID: s for s in ram_chip.SubChips}
    hw_cells = [read_ram_cell(ram_chip, mem_ids, mem_by_id, a)
                for a in range(-13, -8)]
    emu_cells, emu_steps = emu_result()

    print(f"hardware committed {instrs} instructions")
    print(f"hardware RAM[-13..-9] = {hw_cells}")
    print(f"emulator RAM[0..4]     = {emu_cells} after {emu_steps} steps")
    print("PASS" if hw_cells == emu_cells == [1, 2, 3, 4, 5] else "FAIL")


if __name__ == "__main__":
    main()
