"""Chip builder for generating Terbium 65 custom chip JSON files.

A 'ref' is a (owner, pin) tuple:
  owner = subchip instance ID (int) for subchip pins, or boundary pin ID for
          the chip's own pins; pin = pin ID inside that chip (0 for boundary).

Signals:
  1-trit ref  = (owner, pin)
  n-trit bus  = list of refs, index 0 = LSB trit
  wide pin    = single ref whose pin has TritCount n (used where a builtin
                accepts n-trit directly, e.g. Merge/Split/ROM/dev pins)
"""

import json, os, math

REGISTRY = {}          # name(lower) -> chip dict
_next_id = [100000]


def nid():
    _next_id[0] += 1
    return _next_id[0]


class ChipBuilder:
    def __init__(self, name, colour=(0.3, 0.5, 0.7, 1.0)):
        self.name = name
        self.colour = colour
        self.input_pins = []    # dicts
        self.output_pins = []
        self.subchips = []
        self.wires = []
        self._consts = {}       # trit -> (owner,pin)
        self._cursor = [0.0, 0.0]
        # pin positions for boundary pins
        self._pin_pos = {}
        self._auto = []         # subchip dicts placed automatically
        self.lock_output_positions = False

    # ---------------- boundary pins ----------------
    def add_input(self, name, trits, x=None, y=None, display=1):
        pid = nid()
        if x is None:
            y = -2.0 - len(self.input_pins) * 1.2
            x = -6.0
        self.input_pins.append({
            "Name": name, "ID": pid,
            "Position": {"x": round(x, 4), "y": round(y, 4)},
            "TritCount": trits, "Colour": 0, "ValueDisplayMode": display})
        self._pin_pos[pid] = (x, y)
        return pid

    def add_output(self, name, trits, x=None, y=None, display=1):
        pid = nid()
        if x is None:
            y = -2.0 - len(self.output_pins) * 1.2
            x = 6.0
        self.output_pins.append({
            "Name": name, "ID": pid,
            "Position": {"x": round(x, 4), "y": round(y, 4)},
            "TritCount": trits, "Colour": 0, "ValueDisplayMode": display})
        self._pin_pos[pid] = (x, y)
        return pid

    def in_ref(self, pin_id):
        return (pin_id, 0)

    def out_ref(self, pin_id):
        return (pin_id, 0)

    # ---------------- subchips ----------------
    def sub(self, name, x=None, y=None, internal=None, label=""):
        sid = nid()
        auto = x is None
        if auto:
            x = self._cursor[0]
            self._cursor[0] += 1.6
            if self._cursor[0] > 5.0:
                self._cursor[0] = -5.0
                self._cursor[1] -= 1.6
        entry = {
            "Name": name, "ID": sid, "Label": label,
            "Position": {"x": round(x, 4), "y": round(y if y is not None else self._cursor[1], 4)},
            "OutputPinColourInfo": [],
            "InternalData": internal}
        if auto:
            entry["_auto"] = True
            self._auto.append(entry)
        self.subchips.append(entry)
        return sid

    def wire(self, src, dst):
        self.wires.append({
            "SourcePinAddress": {"PinID": src[1], "PinOwnerID": src[0]},
            "TargetPinAddress": {"PinID": dst[1], "PinOwnerID": dst[0]},
            "ConnectionType": 0,
            "ConnectedWireIndex": -1, "ConnectedWireSegmentIndex": -1,
            "Points": [{"x": 0.0, "y": 0.0}, {"x": 0.0, "y": 0.0}]})

    def const(self, trit):
        """Shared constant source -1/0/+1 (1-trit)."""
        if trit not in self._consts:
            name = {-1: "-1", 0: "0", 1: "+1"}[trit]
            sid = self.sub(name, label="")
            self._consts[trit] = (sid, 0)
        return self._consts[trit]

    # ---------------- gate helpers ----------------
    def unary(self, gtype, a, label=""):
        sid = self.sub(gtype, label=label)
        self.wire(a, (sid, 0))
        return (sid, 1)

    def binary(self, gtype, a, b, label=""):
        """a->IN A (id1), b->IN B (id0); returns OUT (id2)."""
        sid = self.sub(gtype, label=label)
        self.wire(b, (sid, 0))
        self.wire(a, (sid, 1))
        return (sid, 2)

    def mem(self, init=1, x=None, y=None, label=""):
        """MEM 1TRIT; init = packed uint (1 = connected 0)."""
        return self.sub("MEM 1TRIT", x=x, y=y, internal=[init], label=label)

    def pulse(self, dur, x=None, y=None):
        return self.sub("PULSE", x=x, y=y, internal=[dur, 0, 0])

    # ---------------- split / merge helpers ----------------
    def split9(self, src9, x=None, y=None, label=""):
        """src9: wide 9-trit ref -> returns list of 9 1-trit refs, LSB first."""
        sid = self.sub("9-1TRIT", x=x, y=y, label=label)
        self.wire(src9, (sid, 0))
        # output pin id = 1+i carries input trit (8-i) -> trit t -> pin 9-t
        return [(sid, 9 - t) for t in range(9)]

    def split3(self, src3, x=None, y=None):
        sid = self.sub("3-1TRIT", x=x, y=y)
        self.wire(src3, (sid, 0))
        return [(sid, 3 - t) for t in range(3)]  # trit t -> pin 3-t

    def merge1to9(self, refs9, x=None, y=None, label=""):
        """refs9: 9 1-trit refs LSB-first -> wide 9-trit ref (pin id 9)."""
        sid = self.sub("1-9TRIT", x=x, y=y, label=label)
        for t in range(9):
            self.wire(refs9[t], (sid, 8 - t))  # trit t <- input pin 8-t
        return (sid, 9)

    def merge1to3(self, refs3, x=None, y=None, label=""):
        sid = self.sub("1-3TRIT", x=x, y=y, label=label)
        for t in range(3):
            self.wire(refs3[t], (sid, 2 - t))
        return (sid, 3)

    def split9to3(self, src9, x=None, y=None):
        """-> (lo3, mid3, hi3) wide 3-trit refs."""
        sid = self.sub("9-3TRIT", x=x, y=y)
        self.wire(src9, (sid, 0))
        return (sid, 3), (sid, 2), (sid, 1)  # out id3=bot? check: id1=top,id2=mid,id3=bot

    def merge3to9(self, lo3, mid3, hi3, x=None, y=None):
        """lo3/mid3/hi3: wide 3-trit refs -> wide 9-trit ref."""
        sid = self.sub("3-9TRIT", x=x, y=y)
        # group0(LSB)->pin id2, group1->id1, group2(MSB)->id0
        self.wire(lo3, (sid, 2))
        self.wire(mid3, (sid, 1))
        self.wire(hi3, (sid, 0))
        return (sid, 3)

    # ---------------- emission ----------------
    def _layout(self):
        """Grid-place auto subchips (creation order kept) and route long
        wires through horizontal/vertical channels. Endpoints of each wire
        are auto-snapped to pins by the app, so only interior Points matter.
        """
        autos = [s for s in self._auto]
        n = len(autos)
        manuals = [s for s in self.subchips if "_auto" not in s]
        # cluster same-type helpers together for readability
        autos.sort(key=lambda s: (s["Name"], s["ID"]))
        if n:
            cols = max(4, math.ceil(math.sqrt(n * 1.5)))
            sx, sy = 2.3, 2.1
            if manuals:
                # helpers band below the manually-placed pipeline
                my = min(s["Position"]["y"] for s in manuals) - 3.5
                xs = [s["Position"]["x"] for s in manuals]
                cx = (min(xs) + max(xs)) / 2
            else:
                my = -1.5
                cx = 0.0
            for i, s in enumerate(autos):
                c, r = i % cols, i // cols
                s["Position"] = {
                    "x": round(cx + (c - (cols - 1) / 2) * sx, 3),
                    "y": round(my - r * sy, 3)}
                del s["_auto"]

        # ---- boundary pins to canvas edges (editing view) ----
        sub_xs = [s["Position"]["x"] for s in self.subchips]
        sub_ys = [s["Position"]["y"] for s in self.subchips]
        if sub_xs:
            min_x, max_x = min(sub_xs) - 1.4, max(sub_xs) + 1.4
            min_y, max_y = min(sub_ys) - 1.4, max(sub_ys) + 1.4
        else:
            min_x = max_x = min_y = max_y = 0.0
        cy = (min_y + max_y) / 2
        span = max_y - min_y

        def place_pins(pins, x, sign):
            m = len(pins)
            if m == 0:
                return
            gap = min(1.1, span / max(m - 1, 1)) if m > 1 else 0
            for i, p in enumerate(pins):
                # pin[0] at top, matching the app's subchip pin convention
                yy = cy - (i - (m - 1) / 2) * gap if m > 1 else cy
                p["Position"] = {"x": round(x, 3), "y": round(yy, 3)}
                self._pin_pos[p["ID"]] = (x, yy)

        place_pins(self.input_pins, min_x - 1.6, 1)
        if self.lock_output_positions:
            for p in self.output_pins:
                self._pin_pos[p["ID"]] = (p["Position"]["x"], p["Position"]["y"])
        else:
            place_pins(self.output_pins, max_x + 1.6, -1)

        # position lookup: subchip id -> centre; boundary pin id -> pos
        pos = {s["ID"]: (s["Position"]["x"], s["Position"]["y"])
               for s in self.subchips}
        pos.update(self._pin_pos)
        sub_by_id = {s["ID"]: s for s in self.subchips}
        bpin = {p["ID"]: (p, True) for p in self.input_pins}
        bpin.update({p["ID"]: (p, False) for p in self.output_pins})

        # ---- exact pin world positions (replicates SubChipInstance layout) ----
        GRID = 0.125
        XOFF_EXTRA = 0.05 / 2 - 0.015   # ChipOutlineWidth/2 - SubChipPinInset

        def local_ys(tritcounts, size_y):
            """Exact replica of CalculatePinLayout LocalPosY values."""
            n = len(tritcounts)
            if n == 1:
                return [0.0]
            grid_y = 0.0
            pin_grid_y = []
            for tc in tritcounts:
                gh = 2 if tc == 1 else 3 if tc == 3 else 4
                pin_grid_y.append(grid_y - gh / 2.0)
                grid_y -= gh
            chip_h = abs(grid_y) * GRID
            ys = [size_y / 2 + g * GRID for g in pin_grid_y]
            space = size_y - chip_h
            if space > 0:
                sp = space / (n - 1)
                for i in range(1, n):
                    ys[i] -= sp * i
            return ys

        def min_chip_h(tritcounts):
            if not tritcounts:
                return 0.0
            return sum(2 if tc == 1 else 3 if tc == 3 else 4
                       for tc in tritcounts) * GRID

        _BUILTIN_SIZE_CACHE = {}

        def chip_size_and_pins(name):
            """-> (w, h, input_pin_list, output_pin_list) or None."""
            desc = REGISTRY.get(name.lower())
            if desc is not None:
                return (desc["Size"]["x"], desc["Size"]["y"],
                        desc["InputPins"], desc["OutputPins"])
            if name in _BUILTIN_SIZE_CACHE:
                return _BUILTIN_SIZE_CACHE[name]
            bd = _builtin_pin_desc(name)
            if bd is None:
                _BUILTIN_SIZE_CACHE[name] = None
                return None
            ins = bd["InputPins"]; outs = bd["OutputPins"]
            u = name.upper()
            if u == "NOT":
                w, h = 1.0, 0.375
            elif u in ("-1", "0", "+1"):
                w, h = 1.0, 0.25
            elif u in ("CLOCK", "PULSE"):
                w, h = 1.0, 0.375
            elif u == "3-STATE BUFFER":
                w, h = 1.5, 0.625
            elif u == "ROM 19683X9":
                w = 2.0
                h = max(min_chip_h([p["TritCount"] for p in ins]),
                        min_chip_h([p["TritCount"] for p in outs]))
            elif "-" in u and "TRIT" in u:   # split/merge chips
                w = 1.125
                h = max(min_chip_h([p["TritCount"] for p in ins]),
                        min_chip_h([p["TritCount"] for p in outs]))
            else:                            # logic gates, MIN/MAX, MEM, etc.
                w, h = 1.0, 0.5
            res = (w, h, ins, outs)
            _BUILTIN_SIZE_CACHE[name] = res
            return res

        def _builtin_pin_desc(name):
            try:
                import csim
            except Exception:
                return None
            ct = csim.BUILTIN_NAME_TO_DESC.get(name.upper())
            if ct is None:
                return None
            return csim.BUILTIN_DESCS.get(ct)

        def pin_world(owner, pid):
            """-> (x, y) exact estimate of the pin's connection point."""
            if owner in bpin:
                p, is_in = bpin[owner]
                x, y = self._pin_pos[owner]
                off = 0.75 if p["TritCount"] <= 3 else 1.125
                return (x + off if is_in else x - off, y)
            sub = sub_by_id.get(owner)
            if sub is None:
                return pos.get(owner)
            cx, cy = sub["Position"]["x"], sub["Position"]["y"]
            info = chip_size_and_pins(sub["Name"])
            if info is None:
                return (cx, cy)
            w, h, ins, outs = info
            side = pins = None
            for i, p in enumerate(ins):
                if p["ID"] == pid:
                    side, pins, idx = "in", ins, i
                    break
            if side is None:
                for i, p in enumerate(outs):
                    if p["ID"] == pid:
                        side, pins, idx = "out", outs, i
                        break
            if side is None:
                return (cx, cy)
            ys = local_ys([p["TritCount"] for p in pins], h)
            xoff = w / 2 + XOFF_EXTRA
            return (cx - xoff if side == "in" else cx + xoff,
                    cy + ys[idx])

        for wi, w in enumerate(self.wires):
            sp = w["SourcePinAddress"]; tp = w["TargetPinAddress"]
            a = pin_world(sp["PinOwnerID"], sp["PinID"])
            t = pin_world(tp["PinOwnerID"], tp["PinID"])
            if not a or not t:
                continue
            dx, dy = t[0] - a[0], t[1] - a[1]
            if abs(dx) + abs(dy) < 1.2:
                continue  # short hop: straight is fine
            jit = ((wi * 37) % 7 - 3) * 0.12
            # orthogonal route: H-V-H or V-H-V through one channel
            if abs(dx) >= abs(dy):
                chan = (a[0] + t[0]) / 2 + jit
                pts = [(chan, a[1]), (chan, t[1])]
            else:
                chan = (a[1] + t[1]) / 2 + jit
                pts = [(a[0], chan), (t[0], chan)]
            w["Points"] = ([{"x": 0.0, "y": 0.0}]
                           + [{"x": round(p[0], 3), "y": round(p[1], 3)}
                              for p in pts]
                           + [{"x": 0.0, "y": 0.0}])

        # ---- display Size: pin-driven like builtin chips ----
        # GridSize = 0.125; pin grid heights: Trit1->2, Trit3->3, Trit9->4.
        def pin_height(pins):
            return sum({1: 2, 3: 3, 9: 4}[p["TritCount"]] for p in pins) * 0.125
        h = max(pin_height(self.input_pins), pin_height(self.output_pins)) + 0.6
        w = max(1.6, min(6.0, 1.2 + 0.22 * len(self.name)))
        self._size = (w, max(1.0, h))

    def emit(self):
        self._layout()
        w, h = self._size
        return {
            "DLSVersion": "2.1.6",
            "Name": self.name,
            "NameLocation": 0,
            "ChipType": 0,
            "Size": {"x": round(w, 3), "y": round(h, 3)},
            "Colour": {"r": self.colour[0], "g": self.colour[1],
                       "b": self.colour[2], "a": self.colour[3]},
            "InputPins": self.input_pins,
            "OutputPins": self.output_pins,
            "SubChips": self.subchips,
            "Wires": self.wires,
            "Displays": [],
        }

    def register(self):
        REGISTRY[self.name.lower()] = self.emit()
        return self.name


def pack_trits(trits):
    """9 trits -> packed uint (PinState encoding, no disconnect flags)."""
    s = 0
    for i, t in enumerate(trits):
        v = {-1: 0, 0: 1, 1: 2}[t]
        s |= v << (i * 2)
    return s


def chip_pin_ids(chip_name):
    """Return {'in': {name: id}, 'out': {name: id}} for a registered chip."""
    d = REGISTRY[chip_name.lower()]
    return ({p["Name"]: p["ID"] for p in d["InputPins"]},
            {p["Name"]: p["ID"] for p in d["OutputPins"]})


def save_project(proj_dir, chip_names, project_name=None):
    os.makedirs(os.path.join(proj_dir, "Chips"), exist_ok=True)
    for nm in chip_names:
        d = REGISTRY[nm.lower()]
        with open(os.path.join(proj_dir, "Chips", nm + ".json"), "w") as f:
            json.dump(d, f, indent=1)
    return d
