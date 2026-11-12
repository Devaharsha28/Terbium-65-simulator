"""Faithful Python replica of the Terbium 65 simulation engine.

Mirrors Assets/Scripts/Simulation/{Simulator,SimChip,SimPin,PinState}.cs:
  - uint pin state: bits 0..17 logic (2 bits/trit), bits 18..26 disconnected flags
  - per-frame processing in readiness order with random fallback for loops
  - builtin chip evaluation identical to ProcessBuiltinChip
  - MEM/PULSE/CLK stateful behaviour identical

Used to verify generated cobalt chips without Unity.
"""

import json, os, random

# ---- PinState helpers (uint encoding) ----
def TritToUint(t):
    return {-1: 0, 0: 1, 1: 2}.get(t, 1)

def UintToTrit(v):
    return {0: -1, 1: 0, 2: 1}.get(v & 3, 0)

def GetTritAtIndex(state, i):
    return UintToTrit((state >> (i * 2)) & 3)

def SetTritAtIndex(state, i, trit):
    state &= ~((3 << (i * 2)) | (1 << (18 + i)))
    return state | (TritToUint(trit) << (i * 2))

def IsTritAtIndexDisconnected(state, i):
    return bool(state & (1 << (18 + i)))

def SetTritAtIndexDisconnected(state, i):
    return state | (1 << (18 + i))

def SetTritValue(state, trit):
    return SetTritAtIndex(state, 0, trit)

def IsTritDisconnected(state):
    return IsTritAtIndexDisconnected(state, 0)

def SetAllDisconnected(state):
    return state | (0x1FF << 18)

def FallbackDisconnectedToZero(state):
    for i in range(9):
        if IsTritAtIndexDisconnected(state, i):
            state = SetTritAtIndex(state, i, 0)
    return state

def GetTritValue(state):
    return UintToTrit(state)

def GetTernaryDecimalValue(state, n):
    v, w = 0, 1
    for i in range(n):
        v += GetTritAtIndex(state, i) * w
        w *= 3
    return v

def HasDisconnectedTrit(state, count):
    return bool(((state >> 18) & ((1 << count) - 1)))

def Set9TritFrom3TritSources(a, b, c):
    bitStates = ((a & 0x3FFFF) & 63) | (((b & 0x3FFFF) & 63) << 6) | (((c & 0x3FFFF) & 63) << 12)
    flags = ((a >> 18) & 7) | (((b >> 18) & 7) << 3) | (((c >> 18) & 7) << 6)
    return (bitStates & 0x3FFFF) | ((flags & 0x1FF) << 18)

def Set3TritFrom9TritSource(state, src, group):
    bitStates = (src >> (group * 6)) & 63
    flags = ((src >> 18) >> (group * 3)) & 7
    return (bitStates & 0x3FFFF) | ((flags & 0x1FF) << 18)

def FromDecimal9(value):
    digits = value + 9841
    state = 0
    for i in range(9):
        state = SetTritAtIndex(state, i, digits % 3 - 1)
        digits //= 3
    return state

def CreateRom9Data(source=None):
    data = [FromDecimal9(0)] * 19683
    if source:
        for i, v in enumerate(source[:19683]):
            data[i] = v
    return data

def FirstBitHigh(state):
    return (not IsTritAtIndexDisconnected(state, 0)) and GetTritAtIndex(state, 0) == 1


# ---- ChipType ints (must match ChipTypes.cs) ----
class CT:
    Custom = 0
    Nand, Not, Min, Max, TriStateBuffer, Clock, Pulse = 1, 2, 3, 4, 5, 6, 7
    dev_Ram_8Bit, Rom_256x16 = 8, 9
    SevenSegmentDisplay, DisplayRGB, DisplayDot, DisplayLED = 10, 11, 12, 13
    Merge_1To3Trit, Merge_1To9Trit, Merge_3To9Trit = 14, 15, 16
    Split_3To1Trit, Split_9To3Trit, Split_9To1Trit = 17, 18, 19
    In_1Trit, In_3Trit, In_9Trit, Out_1Trit, Out_3Trit, Out_9Trit = 20, 21, 22, 23, 24, 25
    Key = 26
    Bus_1Trit, BusTerminus_1Trit, Bus_3Trit, BusTerminus_3Trit, Bus_9Trit, BusTerminus_9Trit = 27, 28, 29, 30, 31, 32
    Buzzer = 33
    Buf, PNot, NNot, Abs, Clu, Cld, Inc, Dec, Rtu, Rtd, Isp, Isz, Isn = 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46
    And, Or, Nor, Cons, NCons, Any, NAny, Mul, NMul, Sum, NSum = 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57
    Rom_19683x9 = 58
    Const_Neg1, Const_Zero, Const_Pos1 = 59, 60, 61
    Mem_1Trit = 62

UNARY = {CT.Buf, CT.Not, CT.PNot, CT.NNot, CT.Abs, CT.Clu, CT.Cld, CT.Inc, CT.Dec,
         CT.Rtu, CT.Rtd, CT.Isp, CT.Isz, CT.Isn}
BINARY = {CT.Min, CT.Max, CT.Nand, CT.And, CT.Or, CT.Nor, CT.Cons, CT.NCons,
          CT.Any, CT.NAny, CT.Mul, CT.NMul, CT.Sum, CT.NSum}
BUS_ORIGIN = {CT.Bus_1Trit, CT.Bus_3Trit, CT.Bus_9Trit}


def EvaluateUnary(t, a):
    if t == CT.Buf: return a
    if t == CT.Not: return -a
    if t == CT.PNot: return -1 if a == 1 else 1
    if t == CT.NNot: return 1 if a == -1 else -1
    if t == CT.Abs: return abs(a)
    if t == CT.Clu: return max(a, 0)
    if t == CT.Cld: return min(a, 0)
    if t in (CT.Inc, CT.Rtu): return -1 if a == 1 else a + 1
    if t in (CT.Dec, CT.Rtd): return 1 if a == -1 else a - 1
    if t == CT.Isp: return 1 if a == 1 else -1
    if t == CT.Isz: return 1 if a == 0 else -1
    if t == CT.Isn: return 1 if a == -1 else -1
    raise ValueError(t)


def EvaluateBinary(t, a, b):
    s = a + b
    ws = s - 3 if s > 1 else (s + 3 if s < -1 else s)
    if t in (CT.Min, CT.And): return min(a, b)
    if t == CT.Nand: return -min(a, b)
    if t in (CT.Max, CT.Or): return max(a, b)
    if t == CT.Nor: return -max(a, b)
    if t == CT.Cons: return a if a == b else 0
    if t == CT.NCons: return -a if a == b else 0
    if t == CT.Any: return max(-1, min(1, s))
    if t == CT.NAny: return -max(-1, min(1, s))
    if t == CT.Mul: return a * b
    if t == CT.NMul: return -a * b
    if t == CT.Sum: return ws
    if t == CT.NSum: return -ws
    raise ValueError(t)


# ---- Sim objects ----
class SimPin:
    __slots__ = ("ID", "isInput", "parentChip", "State", "ConnectedTargetPins",
                 "lastUpdatedFrameIndex", "latestSourceID", "latestSourceParentChipID",
                 "numInputConnections", "numInputsReceivedThisFrame")

    def __init__(self, pid, is_input, parent):
        self.ID = pid
        self.isInput = is_input
        self.parentChip = parent
        self.State = SetAllDisconnected(0)
        self.ConnectedTargetPins = []
        self.lastUpdatedFrameIndex = -1
        self.latestSourceID = -1
        self.latestSourceParentChipID = -1
        self.numInputConnections = 0
        self.numInputsReceivedThisFrame = 0

    def PropagateSignal(self):
        for t in self.ConnectedTargetPins:
            t.ReceiveInput(self)

    def ReceiveInput(self, source):
        global simulationFrame
        if self.lastUpdatedFrameIndex != simulationFrame:
            self.lastUpdatedFrameIndex = simulationFrame
            self.numInputsReceivedThisFrame = 0
        set_ = False
        if self.numInputsReceivedThisFrame > 0:
            for i in range(9):
                if IsTritAtIndexDisconnected(source.State, i):
                    continue
                self.State = SetTritAtIndex(self.State, i, GetTritAtIndex(source.State, i))
                set_ = True
        else:
            self.State = source.State
            set_ = True
        if set_:
            self.latestSourceID = source.ID
            self.latestSourceParentChipID = source.parentChip.ID
        self.numInputsReceivedThisFrame += 1
        if self.isInput and self.numInputsReceivedThisFrame == self.numInputConnections:
            self.parentChip.numInputsReady += 1


class SimChip:
    __slots__ = ("ChipType", "ID", "InternalState", "IsBuiltin", "InputPins",
                 "numConnectedInputs", "numInputsReady", "OutputPins", "SubChips")

    def __init__(self, desc, chip_id, internal_state, subchips):
        self.SubChips = subchips
        self.ID = chip_id
        self.ChipType = desc["ChipType"]
        self.IsBuiltin = self.ChipType != CT.Custom
        self.InputPins = [SimPin(p["ID"], True, self) for p in desc.get("InputPins", [])]
        self.OutputPins = [SimPin(p["ID"], False, self) for p in desc.get("OutputPins", [])]
        self.numConnectedInputs = 0
        self.numInputsReady = 0

        ist = internal_state
        if self.ChipType == CT.Rom_19683x9:
            self.InternalState = CreateRom9Data(ist)
        elif self.ChipType in (CT.DisplayRGB, CT.DisplayDot):
            self.InternalState = [0] * 513
        elif self.ChipType == CT.dev_Ram_8Bit:
            self.InternalState = [random.getrandbits(32) for _ in range(257)]
        elif self.ChipType == CT.Mem_1Trit:
            self.InternalState = [ist[0] if ist else 1]
        elif ist:
            self.InternalState = list(ist)
        else:
            self.InternalState = []

    def Sim_PropagateInputs(self):
        for p in self.InputPins:
            p.PropagateSignal()
            p.State = FallbackDisconnectedToZero(p.State)

    def Sim_PropagateOutputs(self):
        for p in self.OutputPins:
            p.PropagateSignal()
        self.numInputsReady = 0

    def Sim_IsReady(self):
        return self.numInputsReady == self.numConnectedInputs

    def GetSimPinFromAddress(self, addr):
        owner, pid = addr["PinOwnerID"], addr["PinID"]
        for s in self.SubChips:
            if s.ID == owner:
                for p in s.InputPins + s.OutputPins:
                    if p.ID == pid:
                        return p
        for p in self.InputPins + self.OutputPins:
            if p.ID == owner:
                return p
        raise KeyError(f"pin {addr}")

    def GetSimPinFromAddressWithChip(self, addr):
        owner, pid = addr["PinOwnerID"], addr["PinID"]
        for s in self.SubChips:
            if s.ID == owner:
                for p in s.InputPins + s.OutputPins:
                    if p.ID == pid:
                        return p, s
        for p in self.InputPins + self.OutputPins:
            if p.ID == owner:
                return p, None
        raise KeyError(f"pin {addr}")

    def AddConnection(self, src, dst):
        try:
            sp = self.GetSimPinFromAddress(src)
            tp, tc = self.GetSimPinFromAddressWithChip(dst)
            sp.ConnectedTargetPins.append(tp)
            tp.numInputConnections += 1
            if tp.numInputConnections == 1 and tc is not None:
                tc.numConnectedInputs += 1
        except KeyError:
            pass


simulationFrame = 0
stepsPerClockTransition = 250
rng = random.Random(12345)


def RandomBool():
    return rng.random() < 0.5


# ---- builtin chip descriptions (name -> desc dict) ----
def _pd(name, pid, tc, is_in):
    return {"Name": name, "ID": pid, "Position": {"x": 0, "y": 0},
            "TritCount": tc, "Colour": 0, "ValueDisplayMode": 0, "_in": is_in}


def _builtin_desc(chip_type, pins):
    return {
        "ChipType": chip_type,
        "InputPins": [dict(p) for p in pins if p["_in"]],
        "OutputPins": [dict(p) for p in pins if not p["_in"]],
        "SubChips": [], "Wires": [],
    }


def _u_desc(t):
    return _builtin_desc(t, [_pd("IN", 0, 1, True), _pd("OUT", 1, 1, False)])

def _b_desc(t):
    return _builtin_desc(t, [_pd("IN B", 0, 1, True), _pd("IN A", 1, 1, True),
                              _pd("OUT", 2, 1, False)])

BUILTIN_DESCS = {}
for t in (CT.Buf, CT.PNot, CT.NNot, CT.Abs, CT.Clu, CT.Cld, CT.Inc, CT.Dec,
          CT.Rtu, CT.Rtd, CT.Isp, CT.Isz, CT.Isn, CT.Not):
    BUILTIN_DESCS[t] = _u_desc(t)
for t in (CT.Min, CT.Max, CT.Nand, CT.And, CT.Or, CT.Nor, CT.Cons, CT.NCons,
          CT.Any, CT.NAny, CT.Mul, CT.NMul, CT.Sum, CT.NSum):
    BUILTIN_DESCS[t] = _b_desc(t)
BUILTIN_DESCS[CT.TriStateBuffer] = _builtin_desc(CT.TriStateBuffer,
    [_pd("IN", 0, 1, True), _pd("ENABLE", 1, 1, True), _pd("OUT", 2, 1, False)])
BUILTIN_DESCS[CT.Clock] = _builtin_desc(CT.Clock, [_pd("CLK", 0, 1, False)])
BUILTIN_DESCS[CT.Pulse] = _builtin_desc(CT.Pulse,
    [_pd("IN", 0, 1, True), _pd("PULSE", 1, 1, False)])
for t in (CT.Const_Neg1, CT.Const_Zero, CT.Const_Pos1):
    BUILTIN_DESCS[t] = _builtin_desc(t, [_pd("OUT", 0, 1, False)])
BUILTIN_DESCS[CT.Mem_1Trit] = _builtin_desc(CT.Mem_1Trit,
    [_pd("DATA", 0, 1, True), _pd("WE", 1, 1, True), _pd("DATA", 2, 1, False)])
BUILTIN_DESCS[CT.Rom_19683x9] = _builtin_desc(CT.Rom_19683x9,
    [_pd("ADDRESS", 0, 9, True), _pd("DATA", 1, 9, False)])
BUILTIN_DESCS[CT.Split_3To1Trit] = _builtin_desc(CT.Split_3To1Trit,
    [_pd("IN", 0, 3, True), _pd("OUT C", 1, 1, False), _pd("OUT B", 2, 1, False), _pd("OUT A", 3, 1, False)])
BUILTIN_DESCS[CT.Split_9To1Trit] = _builtin_desc(CT.Split_9To1Trit,
    [_pd("IN", 0, 9, True)] + [_pd(f"OUT {c}", i + 1, 1, False) for i, c in enumerate("IHGFEDCBA")])
BUILTIN_DESCS[CT.Split_9To3Trit] = _builtin_desc(CT.Split_9To3Trit,
    [_pd("IN", 0, 9, True), _pd("OUT C", 1, 3, False), _pd("OUT B", 2, 3, False), _pd("OUT A", 3, 3, False)])
BUILTIN_DESCS[CT.Merge_1To3Trit] = _builtin_desc(CT.Merge_1To3Trit,
    [_pd("IN C", 0, 1, True), _pd("IN B", 1, 1, True), _pd("IN A", 2, 1, True), _pd("OUT", 3, 3, False)])
BUILTIN_DESCS[CT.Merge_1To9Trit] = _builtin_desc(CT.Merge_1To9Trit,
    [_pd(f"IN {c}", i, 1, True) for i, c in enumerate("IHGFEDCBA")] + [_pd("OUT", 9, 9, False)])
BUILTIN_DESCS[CT.Merge_3To9Trit] = _builtin_desc(CT.Merge_3To9Trit,
    [_pd("IN C", 0, 3, True), _pd("IN B", 1, 3, True), _pd("IN A", 2, 3, True), _pd("OUT", 3, 9, False)])

BUILTIN_NAME_TO_DESC = {k.upper(): v for k, v in {
    "BUF": CT.Buf, "PNOT": CT.PNot, "NNOT": CT.NNot, "ABS": CT.Abs,
    "CLU": CT.Clu, "CLD": CT.Cld, "INC": CT.Inc, "DEC": CT.Dec,
    "RTU": CT.Rtu, "RTD": CT.Rtd, "ISP": CT.Isp, "ISZ": CT.Isz, "ISN": CT.Isn,
    "AND": CT.And, "OR": CT.Or, "NOR": CT.Nor, "CONS": CT.Cons,
    "NCONS": CT.NCons, "ANY": CT.Any, "NANY": CT.NAny, "MUL": CT.Mul,
    "NMUL": CT.NMul, "SUM": CT.Sum, "NSUM": CT.NSum,
    "NAND": CT.Nand, "NOT": CT.Not, "MIN": CT.Min, "MAX": CT.Max,
    "3-STATE BUFFER": CT.TriStateBuffer, "CLOCK": CT.Clock, "PULSE": CT.Pulse,
    "-1": CT.Const_Neg1, "0": CT.Const_Zero, "+1": CT.Const_Pos1,
    "MEM 1TRIT": CT.Mem_1Trit, "ROM 19683x9": CT.Rom_19683x9,
    "3-1TRIT": CT.Split_3To1Trit, "9-1TRIT": CT.Split_9To1Trit,
    "9-3TRIT": CT.Split_9To3Trit, "1-3TRIT": CT.Merge_1To3Trit,
    "1-9TRIT": CT.Merge_1To9Trit, "3-9TRIT": CT.Merge_3To9Trit,
}.items()}


class Sim:
    """Top-level simulator: library + root chip + frame stepping."""

    def __init__(self, lib, root_desc, root_id=-1, internal=None):
        self.lib = lib
        self.root = self._build(root_desc, root_id, internal)
        self.root_desc = root_desc

    def _desc_for(self, name):
        nm = name.lower()
        if nm in self.lib:
            return self.lib[nm]
        up = name.upper()
        if up in BUILTIN_NAME_TO_DESC:
            return BUILTIN_DESCS[BUILTIN_NAME_TO_DESC[up]]
        raise KeyError(f"unknown chip {name}")

    def _build(self, desc, chip_id, internal):
        subs = []
        for sd in desc.get("SubChips", []):
            subdesc = self._desc_for(sd["Name"])
            subs.append(self._build(subdesc, sd["ID"], sd.get("InternalData")))
        chip = SimChip(desc, chip_id, internal, subs)
        for w in desc.get("Wires", []):
            chip.AddConnection(w["SourcePinAddress"], w["TargetPinAddress"])
        return chip

    def set_input(self, pin_id, trits):
        """Drive a boundary input pin (PinOwnerID=pin_id, PinID=0)."""
        for p in self.root.InputPins:
            if p.ID == pin_id:
                state = 0
                for i, t in enumerate(trits):
                    state = SetTritAtIndex(state, i, t)
                p.State = state
                return
        raise KeyError(pin_id)

    def get_output(self, pin_id):
        for p in self.root.OutputPins:
            if p.ID == pin_id:
                return [GetTritAtIndex(p.State, i) for i in range(9)]
        raise KeyError(pin_id)

    def get_output_state(self, pin_id):
        for p in self.root.OutputPins:
            if p.ID == pin_id:
                return p.State
        raise KeyError(pin_id)

    def find_subchip(self, chip, name):
        for s in chip.SubChips:
            if s._name == name:
                return s
            r = self.find_subchip(s, name)
            if r:
                return r
        return None

    # attach names for debugging
    def _name_tree(self, chip, name):
        chip._name = name
        for s in chip.SubChips:
            pass

    # ---- frame engine (mirrors Simulator.StepChip/Reorder) ----
    def step(self):
        global simulationFrame
        simulationFrame += 1
        self._step_chip_reorder(self.root)

    def _process_builtin(self, chip):
        for p in chip.InputPins:
            p.State = FallbackDisconnectedToZero(p.State)
        t = chip.ChipType
        if t in UNARY:
            inp = chip.InputPins[0].State
            if IsTritDisconnected(inp):
                chip.OutputPins[0].State = SetAllDisconnected(0)
            else:
                chip.OutputPins[0].State = SetTritValue(0, EvaluateUnary(t, GetTritValue(inp)))
        elif t in BINARY:
            a = chip.InputPins[0].State
            b = chip.InputPins[1].State
            if IsTritDisconnected(a) or IsTritDisconnected(b):
                chip.OutputPins[0].State = SetAllDisconnected(0)
            else:
                chip.OutputPins[0].State = SetTritValue(
                    0, EvaluateBinary(t, GetTritValue(a), GetTritValue(b)))
        elif t in (CT.Const_Neg1, CT.Const_Zero, CT.Const_Pos1):
            v = -1 if t == CT.Const_Neg1 else (1 if t == CT.Const_Pos1 else 0)
            chip.OutputPins[0].State = SetTritValue(0, v)
        elif t == CT.Clock:
            high = stepsPerClockTransition != 0 and ((simulationFrame // stepsPerClockTransition) & 1) == 0
            chip.OutputPins[0].State = SetTritValue(0, 1 if high else 0)
        elif t == CT.Pulse:
            ist = chip.InternalState
            while len(ist) < 3:
                ist.append(0)
            inp = chip.InputPins[0].State
            high = FirstBitHigh(inp)
            rem = ist[1]
            if rem == 0 and high and ist[2] == 0:
                rem = ist[0]
                ist[1] = rem
            out = SetTritValue(0, 0)
            if rem > 0:
                ist[1] = rem - 1
                out = SetTritValue(0, 1)
            elif IsTritDisconnected(inp):
                out = SetAllDisconnected(0)
            chip.OutputPins[0].State = out
            ist[2] = 1 if high else 0
        elif t == CT.Split_3To1Trit:
            inp = chip.InputPins[0].State
            for i in range(3):
                out = 0
                out = SetTritAtIndex(out, 0, GetTritAtIndex(inp, 2 - i))
                if IsTritAtIndexDisconnected(inp, 2 - i):
                    out = SetTritAtIndexDisconnected(out, 0)
                chip.OutputPins[i].State = out
        elif t == CT.Merge_1To3Trit:
            out = 0
            for i in range(3):
                ins = chip.InputPins[2 - i].State
                out = SetTritAtIndex(out, i, GetTritAtIndex(ins, 0))
                if IsTritAtIndexDisconnected(ins, 0):
                    out = SetTritAtIndexDisconnected(out, i)
            chip.OutputPins[0].State = out
        elif t == CT.Merge_1To9Trit:
            out = 0
            for i in range(9):
                ins = chip.InputPins[8 - i].State
                out = SetTritAtIndex(out, i, GetTritAtIndex(ins, 0))
                if IsTritAtIndexDisconnected(ins, 0):
                    out = SetTritAtIndexDisconnected(out, i)
            chip.OutputPins[0].State = out
        elif t == CT.Merge_3To9Trit:
            chip.OutputPins[0].State = Set9TritFrom3TritSources(
                chip.InputPins[2].State, chip.InputPins[1].State, chip.InputPins[0].State)
        elif t == CT.Split_9To3Trit:
            inp = chip.InputPins[0].State
            chip.OutputPins[0].State = Set3TritFrom9TritSource(0, inp, 2)
            chip.OutputPins[1].State = Set3TritFrom9TritSource(0, inp, 1)
            chip.OutputPins[2].State = Set3TritFrom9TritSource(0, inp, 0)
        elif t == CT.Split_9To1Trit:
            inp = chip.InputPins[0].State
            for i in range(9):
                out = 0
                out = SetTritAtIndex(out, 0, GetTritAtIndex(inp, 8 - i))
                if IsTritAtIndexDisconnected(inp, 8 - i):
                    out = SetTritAtIndexDisconnected(out, 0)
                chip.OutputPins[i].State = out
        elif t == CT.TriStateBuffer:
            if FirstBitHigh(chip.InputPins[1].State):
                chip.OutputPins[0].State = chip.InputPins[0].State
            else:
                chip.OutputPins[0].State = SetAllDisconnected(0)
        elif t == CT.Key:
            chip.OutputPins[0].State = SetTritValue(0, 1)
        elif t == CT.Rom_19683x9:
            addr = chip.InputPins[0].State
            if HasDisconnectedTrit(addr, 9):
                chip.OutputPins[0].State = SetAllDisconnected(0)
            else:
                idx = GetTernaryDecimalValue(addr, 9) + 9841
                chip.OutputPins[0].State = chip.InternalState[idx]
        elif t == CT.Mem_1Trit:
            we = GetTritValue(chip.InputPins[1].State)
            if we == 1:
                chip.InternalState[0] = chip.InputPins[0].State
            elif we == -1:
                chip.InternalState[0] = 0
            chip.OutputPins[0].State = chip.InternalState[0]
        elif t in (CT.DisplayRGB, CT.DisplayDot, CT.dev_Ram_8Bit, CT.Rom_256x16):
            for p in chip.OutputPins:
                p.State = SetAllDisconnected(0)
        elif t == CT.Buzzer:
            pass
        elif t in BUS_ORIGIN:
            chip.OutputPins[0].State = chip.InputPins[0].State
        else:
            # unknown builtin: outputs stay disconnected
            for p in chip.OutputPins:
                p.State = SetAllDisconnected(0)

    def _step_chip(self, chip):
        chip.Sim_PropagateInputs()
        for sub in reversed(chip.SubChips):
            if sub.IsBuiltin:
                self._process_builtin(sub)
            else:
                self._step_chip(sub)
            sub.Sim_PropagateOutputs()

    def _step_chip_reorder(self, chip):
        chip.Sim_PropagateInputs()
        # mirror StepChipReorder: repeatedly pick next ready subchip
        # (first ready in array order; random fallback if none ready)
        remaining = list(chip.SubChips)
        while remaining:
            nxt = -1
            for i, s in enumerate(remaining):
                if s.Sim_IsReady():
                    nxt = i
                    break
            if nxt < 0:
                nxt = rng.randrange(len(remaining))
            sub = remaining.pop(nxt)
            if sub.IsBuiltin:
                self._process_builtin(sub)
            else:
                self._step_chip_reorder(sub)
            sub.Sim_PropagateOutputs()


def load_library(chips_dir, extra_lib=None):
    lib = {}
    if extra_lib:
        lib.update(extra_lib)
    for fn in os.listdir(chips_dir):
        if fn.endswith(".json"):
            with open(os.path.join(chips_dir, fn)) as f:
                d = json.load(f)
            lib[d["Name"].lower()] = d
    return lib


def state_to_trits(state, n=9):
    return [GetTritAtIndex(state, i) for i in range(n)]


def trits_to_state(trits):
    s = 0
    for i, t in enumerate(trits):
        s = SetTritAtIndex(s, i, t)
    return s
