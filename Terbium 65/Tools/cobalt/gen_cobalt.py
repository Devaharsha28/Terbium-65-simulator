"""Generate the COBALT project: assemble demo program, build COBALT chip,
write project files to TestData/Projects/Cobalt/.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chips, blocks, blocks2, isa

PROJ_DIR = os.path.join("..", "..", "TestData", "Projects", "Cobalt")

DEMO_ASM = """
        LDI.L r1, 1
        LDI.M r1, 0
        LDI.H r1, 0
        LDI.L r2, 2
        LDI.M r2, 0
        LDI.H r2, 0
        ADD r1, r2
        MOV.GA r1, r5
        MOV.AG r3, r5
        HALT
"""


DEMO2_ASM = """
start:
        LDI.L r1, 1
        LDI.M r1, 0
        LDI.H r1, 0
        LDI.L r2, 2
        LDI.M r2, 0
        LDI.H r2, 0
        SHL r1, r2
        MOV.GA r1, r5
        MOV.AG r4, r5
        SHR r4, r2
        RL  r4, r2
        RR  r4, r2
        ADD r4, r2
        SUB r4, r1
        CMP r4, r2
        JG  big
        LDI.L r4, 0
big:    IS  r4, r2
        ANY r4, r2
        CONS r4, r2
        MIN r4, r1
        MAX r4, r1
        MUL r4, r2
        LDI.L r3, 0
        LDI.M r3, 0
        LDI.H r3, 0
        STR r3, r2
        LDA r3, r4
        CMP r4, r1
        JE  eqpath
eqpath: NOP
        HALT
"""


BUBBLE_ASM = """
        LDI.L r1, 5
        MOV.GA r1, r5
        LDI.L r2, -13
        STR r2, r5
        LDI.L r1, 3
        MOV.GA r1, r5
        LDI.L r2, -12
        STR r2, r5
        LDI.L r1, 1
        MOV.GA r1, r5
        LDI.L r2, -11
        STR r2, r5
        LDI.L r1, 4
        MOV.GA r1, r5
        LDI.L r2, -10
        STR r2, r5
        LDI.L r1, 2
        MOV.GA r1, r5
        LDI.L r2, -9
        STR r2, r5

        LDI.L r1, 0
        LDI.L r3, -10
        MOV.GA r3, r9
outer:  LDI.L r2, -13
inner:  CMP r2, r9
        JG done_inner
        MOV.GA r2, r6
        MOV.AG r3, r2
        ADD r3, 1
        MOV.GA r3, r7
        LDA r4, r6
        LDA r3, r7
        CMP r4, r3
        JG swap
        JMP next_j
swap:   MOV.GA r4, r5
        MOV.GA r3, r8
        MOV.AG r4, r6
        STR r4, r8
        MOV.AG r4, r7
        STR r4, r5
next_j: ADD r2, 1
        JMP inner
done_inner:
        MOV.AG r3, r9
        ADD r3, -1
        MOV.GA r3, r9
        ADD r1, 1
        CMP r1, 4
        JL outer
        HALT
"""


def build_all_chips(program):
    chips.REGISTRY.clear()
    chips._next_id[0] = 100000
    for b in blocks.BUILDERS + blocks2.BUILDERS2:
        b()
    blocks2.build_cobalt(program)
    blocks2.build_cobalt_sys(program)
    return chips.REGISTRY


def _pdesc(project_name, chip_names):
    """ProjectDescription matching DLS.Description.ProjectDescription fields."""
    now = "2026-11-08T00:00:00.000+00:00"
    collections = [
        {"Chips": ["NOT", "MIN", "MAX", "CLOCK", "PULSE", "KEY",
                   "3-STATE BUFFER"], "IsToggledOpen": False, "Name": "BASIC"},
        {"Chips": ["NOT", "BUF", "PNOT", "NNOT", "ABS", "CLU", "CLD", "INC",
                   "DEC", "RTU", "RTD", "ISP", "ISZ", "ISN"],
         "IsToggledOpen": False, "Name": "UNARY"},
        {"Chips": ["MIN", "MAX", "NAND", "AND", "OR", "NOR", "CONS", "NCONS",
                   "ANY", "NANY", "MUL", "NMUL", "SUM", "NSUM"],
         "IsToggledOpen": False, "Name": "BINARY"},
        {"Chips": ["-1", "0", "+1"], "IsToggledOpen": False,
         "Name": "CONSTANTS"},
        {"Chips": ["ROM 19683x9", "MEM 1TRIT"], "IsToggledOpen": False,
         "Name": "MEMORY"},
        {"Chips": ["IN-1", "IN-3", "IN-9", "OUT-1", "OUT-3", "OUT-9"],
         "IsToggledOpen": False, "Name": "IN/OUT"},
        {"Chips": ["1-3TRIT", "1-9TRIT", "3-9TRIT", "3-1TRIT", "9-3TRIT",
                   "9-1TRIT"], "IsToggledOpen": False, "Name": "MERGE/SPLIT"},
        {"Chips": ["BUS-1", "BUS-3", "BUS-9"], "IsToggledOpen": False,
         "Name": "BUS"},
        {"Chips": ["7-SEGMENT", "DOT DISPLAY", "RGB DISPLAY", "LED"],
         "IsToggledOpen": False, "Name": "LEGACY DISPLAY"},
        {"Chips": ["ROM 256A-16"], "IsToggledOpen": False,
         "Name": "LEGACY MEMORY"},
        {"Chips": ["BUZZER"], "IsToggledOpen": False, "Name": "LEGACY OTHER"},
    ]
    return {
        "ProjectName": project_name,
        "DLSVersion_LastSaved": "2.1.6",
        "DLSVersion_EarliestCompatible": "2.0.0",
        "CreationTime": now,
        "LastSaveTime": now,
        "Prefs_MainPinNamesDisplayMode": 1,
        "Prefs_ChipPinNamesDisplayMode": 1,
        "Prefs_GridDisplayMode": 1,
        "Prefs_Snapping": 0,
        "Prefs_StraightWires": 0,
        "Prefs_SimPaused": False,
        "Prefs_SimTargetStepsPerSecond": 1000,
        "Prefs_SimStepsPerClockTick": 250,
        "AllCustomChipNames": chip_names,
        "StarredList": [{"Name": "IN/OUT", "IsCollection": True}],
        "ChipCollections": collections,
    }


def write_project(reg, proj_dir, project_name):
    os.makedirs(os.path.join(proj_dir, "Chips"), exist_ok=True)
    names = []
    for nm, d in reg.items():
        fn = os.path.join(proj_dir, "Chips", d["Name"] + ".json")
        with open(fn, "w") as f:
            json.dump(d, f, indent=1)
        names.append(d["Name"])
    pdesc = _pdesc(project_name, names)
    with open(os.path.join(proj_dir, "ProjectDescription.json"), "w") as f:
        json.dump(pdesc, f, indent=1)


def main(asm=BUBBLE_ASM, proj_dir=PROJ_DIR, project_name="Cobalt"):
    program, labels = isa.assemble_program(asm)
    print("program:", len(program), "instructions, labels:", labels)
    reg = build_all_chips(program)
    write_project(reg, proj_dir, project_name)
    print("project written to", proj_dir)


if __name__ == "__main__":
    main()
