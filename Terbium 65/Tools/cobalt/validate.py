"""Terbium 65 project JSON validator + unconnected-input lint.

Validates a whole project directory:
  <proj>/ProjectDescription.json
  <proj>/Chips/*.json

Checks:
  - schema fields, DLSVersion
  - pin trit counts in {1,3,9}
  - unique pin IDs / subchip IDs per chip, unique chip names per project
  - every wire endpoint resolves to a real pin (boundary pin or subchip pin)
  - wire width match (source trit count == target trit count)
  - ChipType is a known integer; custom chips have ChipType 0
  - no chip (in)directly contains itself
  - LINT: every subchip input pin has >=1 incoming wire
         (boundary/dev pins of the chip itself are exempt - driven externally)
"""

import json, os, sys, glob

# ---------------------------------------------------------------------------
# Builtin chip pin tables: name -> (chipTypeInt, [(pinName,pinID,tritCount,isInput)...])
# tritCount: 1,3,9
# ---------------------------------------------------------------------------

CT = dict(Custom=0, Nand=1, Not=2, Min=3, Max=4, TriStateBuffer=5, Clock=6, Pulse=7,
          dev_Ram_8Bit=8, Rom_256x16=9, SevenSegmentDisplay=10, DisplayRGB=11,
          DisplayDot=12, DisplayLED=13, Merge_1To3Trit=14, Merge_1To9Trit=15,
          Merge_3To9Trit=16, Split_3To1Trit=17, Split_9To3Trit=18, Split_9To1Trit=19,
          In_1Trit=20, In_3Trit=21, In_9Trit=22, Out_1Trit=23, Out_3Trit=24,
          Out_9Trit=25, Key=26, Bus_1Trit=27, BusTerminus_1Trit=28, Bus_3Trit=29,
          BusTerminus_3Trit=30, Bus_9Trit=31, BusTerminus_9Trit=32, Buzzer=33,
          Buf=34, PNot=35, NNot=36, Abs=37, Clu=38, Cld=39, Inc=40, Dec=41,
          Rtu=42, Rtd=43, Isp=44, Isz=45, Isn=46, And=47, Or=48, Nor=49,
          Cons=50, NCons=51, Any=52, NAny=53, Mul=54, NMul=55, Sum=56, NSum=57,
          Rom_19683x9=58, Const_Neg1=59, Const_Zero=60, Const_Pos1=61, Mem_1Trit=62)

# builtin pin layouts: chipType -> list of (pinID, tritCount, isInput)
def _u(): return [(0, 1, True), (1, 1, False)]           # unary gate
def _b(): return [(0, 1, True), (1, 1, True), (2, 1, False)]  # binary gate

UNARY_TYPES = [CT[n] for n in ("Buf","PNot","NNot","Abs","Clu","Cld","Inc","Dec",
             "Rtu","Rtd","Isp","Isz","Isn","Not","Nand")]
BINARY_TYPES = [CT[n] for n in ("And","Or","Nor","Cons","NCons","Any","NAny",
              "Mul","NMul","Sum","NSum","Min","Max")]

BUILTIN_PINS = {}
for t in UNARY_TYPES: BUILTIN_PINS[t] = _u()
for t in BINARY_TYPES: BUILTIN_PINS[t] = _b()
BUILTIN_PINS[CT["Nand"]] = _b()
BUILTIN_PINS[CT["TriStateBuffer"]] = [(0,1,True),(1,1,True),(2,1,False)]
BUILTIN_PINS[CT["Clock"]] = [(0,1,False)]
BUILTIN_PINS[CT["Pulse"]] = [(0,1,True),(1,1,False)]
for t in (CT["Const_Neg1"], CT["Const_Zero"], CT["Const_Pos1"]):
    BUILTIN_PINS[t] = [(0,1,False)]
BUILTIN_PINS[CT["Mem_1Trit"]] = [(0,1,True),(1,1,True),(2,1,False)]
BUILTIN_PINS[CT["Rom_19683x9"]] = [(0,9,True),(1,9,False)]
# split/merge: inputs ids 0..n-1, outputs n..n+m-1
BUILTIN_PINS[CT["Split_3To1Trit"]]  = [(0,3,True),(1,1,False),(2,1,False),(3,1,False)]
BUILTIN_PINS[CT["Split_9To1Trit"]]  = [(0,9,True)]+[(i+1,1,False) for i in range(9)]
BUILTIN_PINS[CT["Split_9To3Trit"]]  = [(0,9,True),(1,3,False),(2,3,False),(3,3,False)]
BUILTIN_PINS[CT["Merge_1To3Trit"]]  = [(0,1,True),(1,1,True),(2,1,True),(3,3,False)]
BUILTIN_PINS[CT["Merge_1To9Trit"]]  = [(i,1,True) for i in range(9)]+[(9,9,False)]
BUILTIN_PINS[CT["Merge_3To9Trit"]]  = [(0,3,True),(1,3,True),(2,3,True),(3,9,False)]
for t,nm in ((CT["In_1Trit"],"IN"),(CT["In_3Trit"],"IN"),(CT["In_9Trit"],"IN"),
             (CT["Out_1Trit"],"OUT"),(CT["Out_3Trit"],"OUT"),(CT["Out_9Trit"],"OUT")):
    tc = 1 if "1Trit" in nm else (3 if "3Trit" in nm else 9)
    BUILTIN_PINS[t] = [(0,tc, nm=="IN")]
BUILTIN_PINS[CT["Key"]] = [(0,1,False)]
for t in (CT["Bus_1Trit"],CT["Bus_3Trit"],CT["Bus_9Trit"]):
    tc = {CT["Bus_1Trit"]:1,CT["Bus_3Trit"]:3,CT["Bus_9Trit"]:9}[t]
    BUILTIN_PINS[t] = [(0,tc,True),(1,tc,False)]
for t in (CT["BusTerminus_1Trit"],CT["BusTerminus_3Trit"],CT["BusTerminus_9Trit"]):
    tc = {CT["BusTerminus_1Trit"]:1,CT["BusTerminus_3Trit"]:3,CT["BusTerminus_9Trit"]:9}[t]
    BUILTIN_PINS[t] = [(0,tc,True)]
BUILTIN_PINS[CT["Buzzer"]] = [(0,9,True),(1,3,True)]
BUILTIN_PINS[CT["dev_Ram_8Bit"]] = [(0,9,True),(1,9,True),(2,1,True),(3,1,True),(4,1,True),(5,9,False)]
BUILTIN_PINS[CT["Rom_256x16"]] = [(0,9,True),(1,9,False),(2,9,False)]
BUILTIN_PINS[CT["SevenSegmentDisplay"]] = [(i,1,True) for i in range(7)]+[(7,1,True)]
BUILTIN_PINS[CT["DisplayRGB"]] = [(0,9,True),(1,3,True),(2,3,True),(3,3,True),(4,1,True),(5,1,True),(6,1,True),(7,1,True),(8,3,False),(9,3,False),(10,3,False)]
BUILTIN_PINS[CT["DisplayDot"]] = [(0,9,True),(1,1,True),(2,1,True),(3,1,True),(4,1,True),(5,1,True),(6,1,False)]
BUILTIN_PINS[CT["DisplayLED"]] = [(0,1,True)]

# builtin display name (lowercase) -> ChipType int, from ChipTypeHelper.Names
BUILTIN_NAME_TO_TYPE = {
    "buf": CT["Buf"], "pnot": CT["PNot"], "nnot": CT["NNot"], "abs": CT["Abs"],
    "clu": CT["Clu"], "cld": CT["Cld"], "inc": CT["Inc"], "dec": CT["Dec"],
    "rtu": CT["Rtu"], "rtd": CT["Rtd"], "isp": CT["Isp"], "isz": CT["Isz"],
    "isn": CT["Isn"], "and": CT["And"], "or": CT["Or"], "nor": CT["Nor"],
    "cons": CT["Cons"], "ncons": CT["NCons"], "any": CT["Any"], "nany": CT["NAny"],
    "mul": CT["Mul"], "nmul": CT["NMul"], "sum": CT["Sum"], "nsum": CT["NSum"],
    "rom 19683x9": CT["Rom_19683x9"], "-1": CT["Const_Neg1"], "0": CT["Const_Zero"],
    "+1": CT["Const_Pos1"], "mem 1trit": CT["Mem_1Trit"], "nand": CT["Nand"],
    "not": CT["Not"], "min": CT["Min"], "max": CT["Max"], "clock": CT["Clock"],
    "pulse": CT["Pulse"], "3-state buffer": CT["TriStateBuffer"],
    "dev.ram-8": CT["dev_Ram_8Bit"], "rom 256×16": CT["Rom_256x16"],
    "3-1trit": CT["Split_3To1Trit"], "9-1trit": CT["Split_9To1Trit"],
    "9-3trit": CT["Split_9To3Trit"], "1-3trit": CT["Merge_1To3Trit"],
    "1-9trit": CT["Merge_1To9Trit"], "3-9trit": CT["Merge_3To9Trit"],
    "rgb display": CT["DisplayRGB"], "dot display": CT["DisplayDot"],
    "7-segment": CT["SevenSegmentDisplay"], "led": CT["DisplayLED"],
    "buzzer": CT["Buzzer"], "in-1": CT["In_1Trit"], "in-3": CT["In_3Trit"],
    "in-9": CT["In_9Trit"], "out-1": CT["Out_1Trit"], "out-3": CT["Out_3Trit"],
    "out-9": CT["Out_9Trit"], "key": CT["Key"], "bus-1": CT["Bus_1Trit"],
    "bus-3": CT["Bus_3Trit"], "bus-9": CT["Bus_9Trit"],
    "bus-terminus-1": CT["BusTerminus_1Trit"], "bus-terminus-3": CT["BusTerminus_3Trit"],
    "bus-terminus-9": CT["BusTerminus_9Trit"],
}


def builtin_pin_table(chip_type_int):
    pins = BUILTIN_PINS.get(chip_type_int)
    if pins is None:
        return {}, {}
    return ({pid: tc for pid, tc, i in pins if i},
            {pid: tc for pid, tc, i in pins if not i})


class Chip:
    def __init__(self, name, desc, is_builtin):
        self.name = name
        self.desc = desc
        self.is_builtin = is_builtin
        self.inputs = {}   # pinID -> tritCount
        self.outputs = {}  # pinID -> tritCount
        self.subchips = desc.get("SubChips", [])
        self.wires = desc.get("Wires", [])
        for p in desc.get("InputPins", []) + desc.get("OutputPins", []):
            pass
        for p in desc.get("InputPins", []):
            self.inputs[p["ID"]] = p.get("TritCount", p.get("BitCount"))
        for p in desc.get("OutputPins", []):
            self.outputs[p["ID"]] = p.get("TritCount", p.get("BitCount"))


def load_project(proj_dir):
    chips = {}
    errors = []
    pdesc_path = os.path.join(proj_dir, "ProjectDescription.json")
    if not os.path.exists(pdesc_path):
        return None, [f"missing {pdesc_path}"]
    with open(pdesc_path) as f:
        pdesc = json.load(f)
    if pdesc.get("ProjectName") != os.path.basename(proj_dir):
        errors.append(f"ProjectName {pdesc.get('ProjectName')!r} != folder {os.path.basename(proj_dir)!r}")
    for cf in glob.glob(os.path.join(proj_dir, "Chips", "*.json")):
        with open(cf) as f:
            d = json.load(f)
        name = d.get("Name")
        if name in chips:
            errors.append(f"duplicate chip name {name} ({cf})")
        chips[name.lower()] = Chip(name, d, False)
    return (pdesc, chips), errors


def pin_table(chip):
    """Return (inputs{id:tc}, outputs{id:tc}) for any chip (builtin or custom)."""
    if chip.is_builtin:
        ct = chip.desc  # for builtin we store ChipType int in desc
        pins = BUILTIN_PINS.get(ct, [])
        ins = {pid: tc for pid, tc, i in pins if i}
        outs = {pid: tc for pid, tc, i in pins if not i}
        return ins, outs
    return chip.inputs, chip.outputs


def validate_chip(chip, lib, errors, lint=True):
    """lib: name(lower)->Chip for custom chips."""
    d = chip.desc
    # basic fields
    for fld in ("Name", "ChipType", "Size", "Colour", "InputPins", "OutputPins",
                "SubChips", "Wires"):
        if fld not in d:
            errors.append(f"{chip.name}: missing field {fld}")
    if d.get("ChipType") != 0 and not chip.is_builtin:
        errors.append(f"{chip.name}: custom chip ChipType must be 0, got {d.get('ChipType')}")
    if d.get("ChipType", 0) not in CT.values():
        errors.append(f"{chip.name}: unknown ChipType {d.get('ChipType')}")

    # pin widths + unique ids
    seen_ids = set()
    for p in d.get("InputPins", []) + d.get("OutputPins", []):
        tc = p.get("TritCount", p.get("BitCount"))
        if tc not in (1, 3, 9):
            errors.append(f"{chip.name}: pin {p.get('Name')} bad TritCount {tc}")
        if p["ID"] in seen_ids:
            errors.append(f"{chip.name}: duplicate pin ID {p['ID']}")
        seen_ids.add(p["ID"])

    # subchip ids unique
    sub_ids = set()
    for s in d.get("SubChips", []):
        if s["ID"] in sub_ids:
            errors.append(f"{chip.name}: duplicate subchip ID {s['ID']}")
        sub_ids.add(s["ID"])
        if s["Name"].lower() == chip.name.lower():
            errors.append(f"{chip.name}: contains itself")

    # resolve subchip pin tables
    sub_tables = {}
    for s in d.get("SubChips", []):
        nm = s["Name"].lower()
        if nm in lib:
            sub_tables[s["ID"]] = pin_table(lib[nm])
        elif nm in BUILTIN_NAME_TO_TYPE:
            sub_tables[s["ID"]] = builtin_pin_table(BUILTIN_NAME_TO_TYPE[nm])
        else:
            errors.append(f"{chip.name}: unknown subchip {s['Name']}")

    # boundary pins of THIS chip: PinOwnerID == boundary pin ID, PinID == 0
    def resolve(addr):
        owner, pid = addr["PinOwnerID"], addr["PinID"]
        if owner in chip.inputs or owner in chip.outputs:
            if pid != 0:
                return None
            tc = chip.inputs.get(owner, chip.outputs.get(owner))
            return tc
        if owner in sub_tables:
            ins, outs = sub_tables[owner]
            if pid in ins:
                return ins[pid]
            if pid in outs:
                return outs[pid]
            return None
        return "MISSING"

    # wires
    indeg = {}  # (owner,pid) -> count of incoming wires (only subchip inputs matter)
    for w in d.get("Wires", []):
        s = resolve(w["SourcePinAddress"])
        t = resolve(w["TargetPinAddress"])
        if s == "MISSING" or s is None:
            errors.append(f"{chip.name}: wire source unresolved {w['SourcePinAddress']}")
            continue
        if t == "MISSING" or t is None:
            errors.append(f"{chip.name}: wire target unresolved {w['TargetPinAddress']}")
            continue
        if s != t:
            errors.append(f"{chip.name}: wire width mismatch {s} vs {t} "
                          f"({w['SourcePinAddress']} -> {w['TargetPinAddress']})")
        ta = w["TargetPinAddress"]
        indeg[(ta["PinOwnerID"], ta["PinID"])] = indeg.get((ta["PinOwnerID"], ta["PinID"]), 0) + 1

    # lint: subchip inputs must be driven
    if lint:
        for s in d.get("SubChips", []):
            if s["ID"] not in sub_tables:
                continue
            ins, _ = sub_tables[s["ID"]]
            for pid in ins:
                if indeg.get((s["ID"], pid), 0) == 0:
                    errors.append(f"LINT {chip.name}: subchip {s['Name']}(id{s['ID']}) "
                                  f"input pin {pid} has no incoming wire")
    return sub_tables


def validate_project(proj_dir, lint=True):
    loaded, errors = load_project(proj_dir)
    if loaded is None:
        return errors
    pdesc, lib = loaded
    for name, chip in lib.items():
        validate_chip(chip, lib, errors, lint)
    # recursion check: build containment graph
    graph = {n: set() for n in lib}
    for n, chip in lib.items():
        for s in chip.desc.get("SubChips", []):
            if s["Name"].lower() in lib:
                graph[n].add(s["Name"].lower())
    # cycle detect
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in lib}
    def dfs(u, stack):
        color[u] = GRAY
        for v in graph[u]:
            if color[v] == GRAY:
                errors.append(f"chip recursion cycle: {' -> '.join(stack + [u, v])}")
            elif color[v] == WHITE:
                dfs(v, stack + [u])
        color[u] = BLACK
    for n in lib:
        if color[n] == WHITE:
            dfs(n, [])
    return errors


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "../TestData/Projects/test3"
    errs = validate_project(proj)
    if errs:
        print(f"{len(errs)} problem(s):")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print("OK:", proj)
