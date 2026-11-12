"""Generate TestData/Projects/test3 containing a MUX-27 chip built from gates.

MUX-27: 27:1 ternary multiplexer.
  Inputs : D0-8, D9-17, D18-26 (9-trit each = 27 data trits), SEL (3-trit select)
  Output : Y (1-trit)
  SEL is interpreted as a balanced ternary number v in [-13, 13];
  input index k = v + 13 is selected.

Per select trit j and digit d in {-1,0,+1}: p[j][d] = CLU(IS_d(s_j)) -> +1 iff s_j==d.
Per index k with digits (a2,a1,a0): match = MIN(p2[a2], MIN(p1[a1], p0[a0])),
term = MIN(data_k, match), Y = SUM of all terms (only one term is ever nonzero).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ_DIR = os.path.join(ROOT, "TestData", "Projects", "test3")
CHIPS_DIR = os.path.join(PROJ_DIR, "Chips")

PIN_ID_BASE = 1000
_next_id = [PIN_ID_BASE]


def nid():
    _next_id[0] += 1
    return _next_id[0]


subchips = []   # dicts
wires = []      # dicts
pin_pos = {}    # ownerID -> {pinID: (x,y)} not needed; positions auto for subchips


def add_subchip(name, x, y):
    sid = nid()
    subchips.append({
        "Name": name,
        "ID": sid,
        "Label": "",
        "Position": {"x": x, "y": y},
        "OutputPinColourInfo": [],
        "InternalData": None,
    })
    return sid


def wire(src_owner, src_pin, dst_owner, dst_pin):
    wires.append({
        "SourcePinAddress": {"PinID": src_pin, "PinOwnerID": src_owner},
        "TargetPinAddress": {"PinID": dst_pin, "PinOwnerID": dst_owner},
        "ConnectionType": 0,
        "ConnectedWireIndex": -1,
        "ConnectedWireSegmentIndex": -1,
        "Points": [{"x": 0.0, "y": 0.0}, {"x": 0.0, "y": 0.0}],
    })


# ---- Boundary pins ----
input_pins = []
output_pins = []


def add_pin(name, pin_id, x, y, trit_count, is_input):
    p = {
        "Name": name,
        "ID": pin_id,
        "Position": {"x": x, "y": y},
        "BitCount": trit_count,
        "Colour": 0,
        "ValueDisplayMode": 1,  # Ternary
    }
    (input_pins if is_input else output_pins).append(p)
    return pin_id


data_pin_ids = []
for g, label in enumerate(["D0-8", "D9-17", "D18-26"]):
    data_pin_ids.append(add_pin(label, nid(), -7.0, 2.0 - g * 1.4, 9, True))
sel_pin_id = add_pin("SEL", nid(), -7.0, -3.2, 3, True)
out_pin_id = add_pin("Y", nid(), 7.0, 0.0, 1, False)

# ---- Split chips ----
# 9-1TRIT: input pin id 0 (9-trit); output pin id (i+1) carries trit index (8-i)
# 3-1TRIT: input pin id 0 (3-trit); output pin id (i+1) carries trit index (2-i)
split9_ids = [add_subchip("9-1TRIT", -5.0, 1.4 - g * 1.4) for g in range(3)]
split3_id = add_subchip("3-1TRIT", -5.0, -2.2)

for g in range(3):
    wire(data_pin_ids[g], 0, split9_ids[g], 0)
wire(sel_pin_id, 0, split3_id, 0)


def split9_out(g, trit_idx):
    """pin id on split9[g] output carrying input trit index trit_idx (0=LSB)."""
    i = 8 - trit_idx          # output array index
    return i + 1              # pin id = numIn + i = 1 + i


def split3_out(trit_idx):
    i = 2 - trit_idx
    return i + 1


# data trit k (0..26) -> (split group g, output pin id)
def data_source(k):
    g, t = divmod(k, 9)
    return split9_ids[g], split9_out(g, t)


# select trit j (0=LSB weight1, 1 weight3, 2 weight9) -> (owner, pin)
def sel_source(j):
    return split3_id, split3_out(j)


# ---- Predicate layer: p[j][d] = CLU(IS_d(s_j)) ----
IS_NAME = {1: "ISP", 0: "ISZ", -1: "ISN"}
pred = {}  # (j, d) -> (owner, pin) of CLU output
for j in range(3):
    for d in (-1, 0, 1):
        row = j * 3 + (d + 1)
        is_id = add_subchip(IS_NAME[d], -3.0, 2.0 - row * 0.6)
        clu_id = add_subchip("CLU", -2.3, 2.0 - row * 0.6)
        s_own, s_pin = sel_source(j)
        wire(s_own, s_pin, is_id, 0)
        wire(is_id, 1, clu_id, 0)
        pred[(j, d)] = (clu_id, 1)


# ---- Balanced ternary digits for index k ----
def digits(k):
    """Return (a0,a1,a2) digits at weights 1,3,9 for index k (select value k-13)."""
    v = k - 13
    for a2 in (-1, 0, 1):
        for a1 in (-1, 0, 1):
            a0 = v - a2 * 9 - a1 * 3
            if -1 <= a0 <= 1:
                return (a0, a1, a2)
    raise ValueError(k)


def digit_at(k, j):
    return digits(k)[j]


# ---- Match + term + sum tree ----
terms = []
y = -3.4
for k in range(27):
    # lo = MIN(p[1][a1], p[0][a0]); match = MIN(p[2][a2], lo)
    lo_id = add_subchip("MIN", -0.6, y)
    m_id = add_subchip("MIN", 0.7, y)
    t_id = add_subchip("MUL", 2.0, y)  # data * match: match=+1 -> data, match=0 -> 0

    p10 = pred[(1, digit_at(k, 1))]
    p00 = pred[(0, digit_at(k, 0))]
    p20 = pred[(2, digit_at(k, 2))]

    wire(p10[0], p10[1], lo_id, 0)
    wire(p00[0], p00[1], lo_id, 1)

    wire(p20[0], p20[1], m_id, 0)
    wire(lo_id, 2, m_id, 1)

    d_own, d_pin = data_source(k)
    wire(d_own, d_pin, t_id, 0)
    wire(m_id, 2, t_id, 1)

    terms.append((t_id, 2))
    y -= 0.55


# SUM chain: acc = SUM(term0, term1); acc = SUM(acc, term_k)
acc_owner, acc_pin = terms[0]
for k in range(1, 27):
    s_id = add_subchip("SUM", 3.6, -3.4 - (k - 1) * 0.55)
    t_own, t_pin = terms[k]
    wire(acc_owner, acc_pin, s_id, 0)
    wire(t_own, t_pin, s_id, 1)
    acc_owner, acc_pin = s_id, 2

wire(acc_owner, acc_pin, out_pin_id, 0)

chip = {
    "DLSVersion": "2.1.6",
    "Name": "MUX-27",
    "NameLocation": 0,
    "ChipType": 0,
    "Size": {"x": 6.0, "y": 4.0},
    "Colour": {"r": 0.3, "g": 0.5, "b": 0.7, "a": 1.0},
    "InputPins": input_pins,
    "OutputPins": output_pins,
    "SubChips": subchips,
    "Wires": wires,
    "Displays": [],
}

os.makedirs(CHIPS_DIR, exist_ok=True)
with open(os.path.join(CHIPS_DIR, "MUX-27.json"), "w") as f:
    json.dump(chip, f, indent=1)

project = {
    "ProjectName": "test3",
    "DLSVersion_LastSaved": "2.1.6",
    "DLSVersion_EarliestCompatible": "2.0.0",
    "CreationTime": "2026-11-08T00:00:00.000+00:00",
    "LastSaveTime": "2026-11-08T00:00:00.000+00:00",
    "Prefs_MainPinNamesDisplayMode": 1,
    "Prefs_ChipPinNamesDisplayMode": 1,
    "Prefs_GridDisplayMode": 1,
    "Prefs_Snapping": 0,
    "Prefs_StraightWires": 0,
    "Prefs_SimPaused": False,
    "Prefs_SimTargetStepsPerSecond": 1000,
    "Prefs_SimStepsPerClockTick": 250,
    "AllCustomChipNames": ["MUX-27"],
    "StarredList": [
        {"Name": "IN/OUT", "IsCollection": True},
        {"Name": "MUX-27", "IsCollection": False},
    ],
    "ChipCollections": [
        {"Chips": ["NOT", "MIN", "MAX", "CLOCK", "PULSE", "KEY", "3-STATE BUFFER"], "IsToggledOpen": False, "Name": "BASIC"},
        {"Chips": ["NOT", "BUF", "PNOT", "NNOT", "ABS", "CLU", "CLD", "INC", "DEC", "RTU", "RTD", "ISP", "ISZ", "ISN"], "IsToggledOpen": False, "Name": "UNARY"},
        {"Chips": ["MIN", "MAX", "NAND", "AND", "OR", "NOR", "CONS", "NCONS", "ANY", "NANY", "MUL", "NMUL", "SUM", "NSUM"], "IsToggledOpen": False, "Name": "BINARY"},
        {"Chips": ["-1", "0", "+1"], "IsToggledOpen": False, "Name": "CONSTANTS"},
        {"Chips": ["ROM 19683x9", "MEM 1TRIT"], "IsToggledOpen": False, "Name": "MEMORY"},
        {"Chips": ["IN-1", "IN-3", "IN-9", "OUT-1", "OUT-3", "OUT-9"], "IsToggledOpen": False, "Name": "IN/OUT"},
        {"Chips": ["1-3TRIT", "1-9TRIT", "3-9TRIT", "3-1TRIT", "9-3TRIT", "9-1TRIT"], "IsToggledOpen": False, "Name": "MERGE/SPLIT"},
        {"Chips": ["BUS-1", "BUS-3", "BUS-9"], "IsToggledOpen": False, "Name": "BUS"},
        {"Chips": ["7-SEGMENT", "DOT DISPLAY", "RGB DISPLAY", "LED"], "IsToggledOpen": False, "Name": "LEGACY DISPLAY"},
        {"Chips": ["ROM 256×16"], "IsToggledOpen": False, "Name": "LEGACY MEMORY"},
        {"Chips": ["BUZZER"], "IsToggledOpen": False, "Name": "LEGACY OTHER"},
    ],
}

with open(os.path.join(PROJ_DIR, "ProjectDescription.json"), "w") as f:
    json.dump(project, f, indent=1)

print(f"Wrote {len(subchips)} subchips, {len(wires)} wires -> {CHIPS_DIR}\\MUX-27.json")
