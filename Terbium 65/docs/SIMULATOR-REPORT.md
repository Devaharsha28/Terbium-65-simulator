# Terbium 65 — Complete Simulator Report

This document describes the entire Terbium 65 codebase: what it is, how every
subsystem works, naming conventions, data formats, and file map. It is detailed
enough to reimplement or deeply modify the simulator.

---

## 1. What Terbium 65 Is

Terbium 65 is a **visual digital-logic circuit simulator for balanced ternary
computing**, built as a fork/modification of Sebastian Lague's
*Digital Logic Sim* (DLS). It runs on **Unity 6000.6.0f1 (Unity 6), C#**.

Instead of binary `0/1`, every signal trit carries one of three logic values:

| Trit | Meaning |
|---:|---|
| `-1` | Negative |
| `0` | Neutral |
| `+1` | Positive |

A "disconnected" (floating) condition is tracked **separately** from the logic
value — it is not a fourth logic state. (Note: as of the latest changes, a
disconnected trit on a *chip input pin* falls back to `0` at evaluation time;
disconnection still exists as a wire/pin state and is displayed distinctly.)

App version: `DLSVersion = 2.1.6`, earliest compatible `2.0.0`
(`Main.DLSVersion`, `Assets/Scripts/Game/Main/Main.cs`).

---

## 2. Repository Layout

```
Terbium 65/
├── Assets/
│   ├── Scripts/
│   │   ├── Description/        Data model types + JSON serialization
│   │   ├── Game/               Project, chips, elements, interaction, audio
│   │   ├── Graphics/           Drawing, themes, all UI menus
│   │   ├── SaveSystem/         Load/save of projects and chips
│   │   ├── Seb/                Vendored Sebastic utility lib (maths, UI
│   │   │                        primitives, fonts, input abstraction)
│   │   └── Simulation/         The simulation engine (pure C#, no Unity deps)
│   ├── Resources/, Settings/, Build/, Dev/
├── TestData/                   Editor-mode save directory
│   ├── Projects/<name>/ProjectDescription.json
│   ├── Projects/<name>/Chips/<chip>.json
│   ├── Deleted Projects/
│   └── AppSettings.json
├── Packages/manifest.json      Unity packages (see §12)
├── ProjectSettings/            Unity project settings
├── Tools/gen_mux27.py          Python generator that authored test3/MUX-27
├── docs/                       Documentation (this file, SPECIFICATIONS.md)
├── SPECIFICATIONS.md           Formal ternary spec (gates, representations)
├── README.md                   User-facing overview
└── Build_linux/, build_win/    Previous build outputs
```

---

## 3. Core Data Model

### 3.1 Trit state encoding (`PinState`)

File: `Assets/Scripts/Simulation/PinState.cs`

Every pin's state is a single `uint` (32 bits):

```
bits  0..17 : logic values — 2 bits per trit, 9 trits max
              encoding per trit: 00 → -1, 01 → 0, 10 → +1, 11 → treated as 0
bits 18..26 : disconnected flags — 1 bit per trit (1 = disconnected)
bit  27+    : unused
```

Key constants/methods:

- `TritNegative=-1`, `TritZero=0`, `TritPositive=1` (sbyte)
- `TritToUint`/`UintToTrit` — trit ↔ 2-bit logic value
- `GetTritAtIndex(state,i)`, `SetTritAtIndex`, `IsTritAtIndexDisconnected`,
  `SetTritAtIndexDisconnected`
- `SetTritValue`/`GetTritValue` — trit index 0 convenience wrappers
- `SetAllDisconnected(state)` — sets all 9 flag bits
- `FallbackDisconnectedToZero(state)` — replaces each disconnected trit with a
  connected `0` (**added in this fork**; applied to every chip input)
- `GetTritValue`, `GetTernaryDecimalValue(state, n)` — Σ trit·3^i
- `HasDisconnectedTrit(state, count)`
- `FormatTernary(state, count, buf)` — writes `-`/`0`/`+`/`Z` chars
- `FormatGrouped(state, count, groupSize, buf)` — nonary (`a`-`i`) and hept
  grouped display; `?` for disconnected groups
- `FromDecimal9(value)` / `CreateRom9Data()` — balanced-ternary ↔ index encoding
  for the 19683×9 ROM (packed zero = -9841)

### 3.2 Pin widths

`PinTritCount` enum: `Trit1=1`, `Trit3=3`, `Trit9=9`. Only these three widths
are supported; the serializer rejects others (1/3/9 check in
`Serializer.DeserializeChipDescription`).

### 3.3 Number representations

`PinState.FormatTernary` / `FormatGrouped` implement the display formats
documented in SPECIFICATIONS.md §4/§13/§14:

- **Balanced Ternary** — `-`,`0`,`+` per trit (Z = disconnected)
- **Decimal** — `GetTernaryDecimalValue` = Σ trit·3^i (balanced → negative possible)
- **Balanced Nonary** — groups of 3 trits → digit 0-8 mapped `a`..`i`
  (value v∈[-13,13] → `a`+v)
- **Hept** — groups of 3 trits mapped differently (see SPECIFICATIONS §14)

### 3.4 Description types (`Assets/Scripts/Description/Types/`)

All are plain `[Serializable]` structs/classes serialized by Newtonsoft.Json:

- **`ChipDescription`** (class) — a chip *type*: `Name`, `NameLocation`
  (Centre/Top/Hidden), `ChipType` (enum), `Size` (Vector2), `Colour`,
  `InputPins[]`, `OutputPins[]`, `SubChips[]`, `Wires[]`, `Displays[]`,
  `DLSVersion`. `ChipType.Custom=0` for player chips.
- **`PinDescription`** (struct) — `Name`, `ID` (unique within parent chip),
  `Position` (Vector2, used for dev-pin layout), `TritCount`, `Colour`
  (PinColour enum: Red,Orange,Yellow,Green,Blue,Violet,Pink,White),
  `ValueDisplayMode` (Off/Ternary/Decimal/Nonary/Hept).
  *Serialization note:* JSON field is `TritCount`; legacy files may contain
  `BitCount` — the deserializer migrates it (rejecting widths other than 1/3/9).
- **`SubChipDescription`** (struct) — an *instance* of a chip inside a parent:
  `Name` (references a ChipDescription by name), `ID` (unique within parent,
  >0), `Label`, `Position`, `OutputPinColourInfo[]` (per-output-pin colour
  overrides), `InternalData` (uint[] — ROM contents, key binding, pulse params,
  bus linkage, etc.).
- **`WireDescription`** (struct) — `SourcePinAddress`, `TargetPinAddress`
  (PinAddress), `ConnectionType` (ToPins / ToWireSource / ToWireTarget —
  wires can join other wires), `ConnectedWireIndex`,
  `ConnectedWireSegmentIndex`, `Points[]` (Vector2 polyline; zeros = auto-route).
- **`PinAddress`** (struct) — `{PinOwnerID, PinID}`. For dev pins:
  `PinOwnerID` = dev pin element ID, `PinID` = 0. For subchip pins:
  `PinOwnerID` = subchip instance ID, `PinID` = the pin's ID inside that chip.
- **`ProjectDescription`** (struct) — project metadata + prefs +
  `AllCustomChipNames[]`, `StarredList`, `ChipCollections` (named groups of
  chip names shown in the bottom bar).
- **`AppSettings`** — resolution, fullscreen mode, VSync.

### 3.5 ChipType enum (`Description/Types/SubTypes/ChipTypes.cs`)

Serialized as **integer** — new values must be appended at the end to preserve
IDs of saved projects. Current order:

```
Custom,
// Basic: Nand, Not, Min, Max, TriStateBuffer, Clock, Pulse
// Memory: dev_Ram_8Bit, Rom_256x16
// Displays: SevenSegmentDisplay, DisplayRGB, DisplayDot, DisplayLED
// Merge/Split: Merge_1To3Trit, Merge_1To9Trit, Merge_3To9Trit,
//              Split_3To1Trit, Split_9To3Trit, Split_9To1Trit
// I/O pins: In_1Trit, In_3Trit, In_9Trit, Out_1Trit, Out_3Trit, Out_9Trit
Key,
// Buses: Bus_1Trit, BusTerminus_1Trit, Bus_3Trit, BusTerminus_3Trit,
//        Bus_9Trit, BusTerminus_9Trit
Buzzer,
// Appended (ternary additions — order matters!):
Buf, PNot, NNot, Abs, Clu, Cld, Inc, Dec, Rtu, Rtd, Isp, Isz, Isn,
And, Or, Nor, Cons, NCons, Any, NAny, Mul, NMul, Sum, NSum,
Rom_19683x9,
Const_Neg1, Const_Zero, Const_Pos1,   // constant sources (added)
Mem_1Trit                            // 1-trit memory element (added)
```

`ChipTypeHelper` (`Description/Helpers/ChipTypeHelper.cs`) maps each type to a
display name (dictionary `Names`; `GetName` throws if missing — every enum value
must have an entry). Also provides `IsBusType`, `IsBusOriginType`,
`IsBusTerminusType`, `IsRomType`, `GetPinType`, `IsInputOrOutputPin`.

---

## 4. Component Catalog

All builtin chip descriptions are created in
`Game/Project/BuiltinChipCreator.cs` (`CreateAllBuiltinChipDescriptions()`),
and their menu grouping in `BuiltinCollectionCreator.cs`.

### 4.1 Logic gates (unary — 1 input `IN` id0, 1 output `OUT` id1)

| Name | ChipType | Function (sbyte trit math) |
|---|---|---|
| BUF | Buf | identity |
| NOT | Not | negate (-a) |
| PNOT | PNot | +1→-1, else +1 ("is positive"→invert) |
| NNOT | NNot | -1→+1, else -1 |
| ABS | Abs | \|a\| |
| CLU | Clu | max(a,0) — clamp low |
| CLD | Cld | min(a,0) — clamp down |
| INC | Inc | a==+1→-1 else a+1 (rotate up) |
| DEC | Dec | a==-1→+1 else a-1 (rotate down) |
| RTU | Rtu | same as INC |
| RTD | Rtd | same as DEC |
| ISP | Isp | a==+1 → +1 else -1 |
| ISZ | Isz | a==0 → +1 else -1 |
| ISN | Isn | a==-1 → +1 else -1 |

### 4.2 Logic gates (binary — inputs `IN B` id0, `IN A` id1, output `OUT` id2)

| Name | ChipType | Function |
|---|---|---|
| MIN / AND | Min, And | min(a,b) — note AND==MIN in ternary |
| MAX / OR | Max, Or | max(a,b) |
| NAND | Nand | -min(a,b) |
| NOR | Nor | -max(a,b) |
| CONS | Cons | a==b ? a : 0 |
| NCONS | NCons | a==b ? -a : 0 |
| ANY | Any | clamp(sum,-1,1) where sum=a+b |
| NANY | NAny | -clamp(sum) |
| MUL | Mul | a*b |
| NMUL | NMul | -a*b |
| SUM | Sum | wrapped sum: a+b ∈{-2..2} wrapped mod 3 into {-1,0,1} |
| NSUM | NSum | -wrapped sum |

Truth tables: SPECIFICATIONS.md §6–§7.

### 4.3 Other builtin components

| Name | ChipType | Pins | Behavior |
|---|---|---|---|
| CLOCK | Clock | OUT `CLK` | toggles +1/0 every `stepsPerClockTransition` sim frames |
| PULSE | Pulse | IN, OUT `PULSE` | on rising edge of IN, outputs +1 for `InternalState[0]` ticks (default 50); edge-detect via stored prev state |
| KEY | Key | OUT | +1 while bound key (A–Z, 0–9) held, else -1; binding in InternalState[0], editable via context menu |
| 3-STATE BUFFER | TriStateBuffer | IN, ENABLE, OUT | OUT=IN when ENABLE is +1, else disconnected |
| Split/Merge | Split_3To1Trit, Split_9To1Trit, Split_9To3Trit, Merge_1To3Trit, Merge_1To9Trit, Merge_3To9Trit | various | repack trits between widths; per-trit disconnect preserved |
| ROM 19683x9 | Rom_19683x9 | ADDRESS (9t), DATA (9t) | 3^9=19683 entries; balanced address -9841..+9841 → index addr+9841; unconnected address → (now) 0 fallback; contents in InternalState, editable via ROM editor |
| ROM 256×16 | Rom_256x16 | ADDRESS (9t), OUT A/B (9t) | legacy binary ROM, currently outputs disconnected (legacy semantics disabled) |
| dev.RAM-8 | dev_Ram_8Bit | ADDRESS,DATA,WRITE,RESET,CLOCK (9t/9t/1t) → OUT | hidden chip; legacy, outputs disconnected |
| DOT/RGB/7-SEG/LED displays | Display* | various | legacy displays; sim outputs disconnected (not ternary-enabled) |
| Buzzer | Buzzer | PITCH(9t), VOLUME(3t) | non-functional (silent stub) |
| BUS-1/3/9 + BUS-TERMINUS-* | Bus_*/BusTerminus_* | hidden in / out | virtual bus: origin copies input→output; terminus is the visible endpoint; pair linked via InternalData[0]=pair ID, InternalData[1]=flip flag; terminus chips hidden from library |
| **-1 / 0 / +1** | Const_Neg1/Zero/Pos1 | OUT | constant trit source, no inputs (**added**) |
| **MEM 1TRIT** | Mem_1Trit | DATA, WE → DATA | 1-trit latch: WE=+1 write DATA, WE=0 hold, WE=-1 clear to 0; InternalState[0] holds packed state, init connected-0 (**added**) |

IN-x / OUT-x "chips" are **not subchips** — placing them creates a
`DevPinInstance` (a boundary pin of the chip being edited). See §6.

Menu collections (`BuiltinCollectionCreator`): BASIC, UNARY, BINARY,
CONSTANTS, MEMORY, IN/OUT, MERGE/SPLIT, BUS, LEGACY DISPLAY, LEGACY MEMORY,
LEGACY OTHER.

---

## 5. Simulation Engine (`Assets/Scripts/Simulation/`)

Pure C# — no UnityEngine dependency (except `Debug` in a couple of places).

### 5.1 Threading model

- `Project.SimThread()` runs on a dedicated background thread
  (`DLS_SimThread`, highest priority). The main thread only *enqueues*
  modifications and *reads* display state.
- Each sim "tick" = one `Simulator.RunSimulationStep(rootSimChip, inputPins, simAudio)`.
- Target rate: `Prefs_SimTargetStepsPerSecond` (default 1000 ticks/s); the sim
  thread busy-waits (`Thread.SpinWait`) to hit it. Pause = `Prefs_SimPaused`;
  Space (unpaused) = advance single step via `advanceSingleSimStep`.
- `stepsPerClockTransition` = `Prefs_SimStepsPerClockTick` (default 250) —
  CLOCK period in sim ticks; also used by PULSE timing.
- `debug_runSimMainThread` flag can run sim on main thread for debugging.

### 5.2 Frame algorithm (`Simulator.RunSimulationStep` → `StepChip`/`StepChipReorder`)

Documented in code comments (Simulator.cs ~line 32):

1. Copy player-controlled dev-pin input states into the root sim chip's pins
   (`PinState.Set(ref simPin.State, input.Pin.PlayerInputState)`).
2. Propagate: for each chip, forward input-pin states inward, then process
   subchips in an order determined by readiness.
3. A chip is **ready** when every connected input pin has received all its
   wire inputs this frame (`SimPin.numInputsReceivedThisFrame ==
   numInputConnections`, tracked via `SimChip.numConnectedInputs` /
   `numInputsReady`). Unconnected pins (0 connections) are always ready.
4. `StepChipReorder` (used on first frame / after any modification,
   `needsOrderPass`) topologically sorts subchips by readiness. Subsequent
   frames use `StepChip` which walks the cached order.
5. If no subchip is ready (combinational loop / sequential feedback), one is
   picked **at random** — race conditions resolve nondeterministically. Every
   100 frames (`canDynamicReorderThisFrame`) adjacent non-ready chips may be
   swapped to vary race outcomes (SR-latch style races).
6. Bus-origin chips are processed last in the random fallback (they need all
   inputs before display).

### 5.3 Pins (`SimPin`)

- `State` (uint, §3.1), `ConnectedTargetPins[]` (downstream pins this pin
  drives), `numInputConnections`, `numInputsReceivedThisFrame`,
  `latestSourceID`/`latestSourceParentChipID` (for wire colouring),
  `lastUpdatedFrameIndex`.
- `ReceiveInput(source)`: first source of the frame wins wholesale; additional
  sources merge **per-trit** — a later source can only overwrite trits that are
  *not* disconnected in its own state ("floating sources must not erase driven
  trits"). Conflicting driven sources keep last-arrival-wins per trit.
- `PropagateSignal()` pushes `State` to all `ConnectedTargetPins`.

### 5.4 Chips (`SimChip`)

- `ChipType`, `ID`, `IsBuiltin` (= ChipType != Custom), `InputPins[]`,
  `OutputPins[]`, `SubChips[]` (recursive hierarchy), `InternalState` (uint[]
  per-instance data), `numConnectedInputs`/`numInputsReady`.
- Constructor builds pins from `PinDescription`s and initializes
  `InternalState` per type: ROM_19683x9 → 19683 trit-words; displays →
  512+1 buffer; dev_Ram → 257 random; Mem_1Trit → 1 word (init connected 0);
  otherwise copies serialized `internalState` if present.
- `Sim_PropagateInputs()` forwards each input pin's state to its targets AND
  applies `PinState.FallbackDisconnectedToZero` (**new behaviour**).
- `Sim_PropagateOutputs()` forwards output pins and resets `numInputsReady`.
- `AddConnection`/`RemoveConnection` maintain `ConnectedTargetPins` and the
  ready-count bookkeeping; removing the last connection marks the target pin
  fully disconnected.

### 5.5 Gate evaluation (`Simulator.ProcessBuiltinChip`)

- **Every builtin chip's input pins are first sanitized**: each input pin's
  `State` gets `FallbackDisconnectedToZero` — missing/floating inputs read as
  `0` (**new behaviour**; previously disconnected inputs produced disconnected
  outputs).
- Unary/binary gates evaluate trit 0 via `EvaluateUnary`/`EvaluateBinary`
  (sbyte math, §4.1–4.2). The old "if input disconnected → output disconnected"
  branches still exist but are unreachable for inputs.
- Special cases: Clock (square wave from frame counter), Pulse (edge + tick
  counter), Split/Merge (per-trit repack preserving disconnect flags),
  TriStateBuffer (enable=+1 passes data else disconnects), Key (keyboard
  lookup), ROM_19683x9 (address→index, outputs stored word), constants
  (drive fixed trit), Mem_1Trit (WE truth table, §4.3), legacy
  display/RAM/ROM256 → all outputs forced disconnected, Buzzer → no-op,
  bus origins → copy input to output.
- `EvaluateBinary` wraps SUM: `sum=a+b; wrapped = sum>1? sum-3 : sum<-1? sum+3 : sum`.

### 5.6 Thread-safe modification queue

Main thread calls `Simulator.AddPin/RemovePin/AddSubChip/AddConnection/
RemoveConnection/RemoveSubChip` → enqueues `SimModifyCommand`; sim thread
drains via `ApplyModifications()` each tick and sets `needsOrderPass=true`
(re-sort next frame). This is how live editing doesn't corrupt the sim.

### 5.7 Randomness

`System.Random rng` + a PCG-style `pcg_rngState` (`RandomBool()`) seeded per
frame from `rng.Next()` — used for race-condition ordering.

### 5.8 Audio hook

`SimAudio` (`Simulation/SimAudio.cs`) collects note requests per frame
(`RegisterNote(index, volume)`); `NotifyAllNotesRegistered(deltaTime)`
smooths amplitudes. Only the (non-functional) Buzzer was meant to use it.
`SimKeyboardHelper` snapshots held keys (A–Z,0–9) on the main thread for KEY
chips (`KeyIsHeld` on sim thread, lock-guarded).

---

## 6. Editing Model & Elements (`Game/`)

### 6.1 Dev pins vs subchips

- **Dev pins** (`DevPinInstance`): boundary pins of the chip being edited —
  created by placing IN-x/OUT-x "chips". Input dev pins are player-controlled:
  clicking their state display cycles trits (`-1→0→+1→-1` per click,
  `PinState.Toggle`); `PlayerInputState` is copied into sim each frame.
  Output dev pins just display driven values.
- **Subchips** (`SubChipInstance`): placed chip instances; pins auto-laid-out
  vertically by `CalculatePinLayout` based on chip `Size.y` and pin heights
  (Trit1=2 grid, Trit3=3, Trit9=4 grid units × GridSize=0.125).
- **Wires** (`WireInstance`): connect a source pin to a target pin
  (`WireConnectionType.ToPins`), or to another wire (`ToWireSource`/
  `ToWireTarget` — wire junctions). `Points` polyline; zeros mean auto-route.
  Bus wires are wires attached to bus pins.

### 6.2 Chip hierarchy & view stack

`Project.chipViewStack` (Stack<DevChipInstance>): bottom = chip being edited;
pushing = "view mode" into a subchip's internals (read-only, `CanEditViewedChip`
false when depth>1). `EnterViewMode`/`ReturnToPreviousViewedChip`.

`DevChipInstance` = the editable circuit: `Elements` (pins+subchips), `Wires`,
`UndoController`, `LastSavedDescription`, `SimChip` link, `AllParentChipNames`
(recursion guard for chip-in-chip).

### 6.3 Project lifecycle (`Project.cs`, `Main.cs`)

- `Main.CreateOrLoadProject(name, startupChipName)` → load or create
  `ProjectDescription`, build `ChipLibrary` (custom chips from `Chips/*.json` +
  all builtin descriptions; bus terminators & dev_Ram hidden), open dev chip.
- `ChipLibrary` (`Game/Project/ChipLibrary.cs`): name→description lookup
  (case-insensitive), `GetDirectParentChips` (used when a chip is renamed/
  deleted — all parents are loaded, patched, and resaved).
- `UpdateAndSaveAffectedChips`: on chip rename/delete/pin-removal, every parent
  chip containing it is updated and resaved automatically.
- Sim notifications: `NotifyKeyChipBindingChanged`, `NotifyPulseWidthChanged`,
  `NotifyRomContentsEdited`, `NotifyLEDColourChanged` patch live `SimChip`s.

### 6.4 Saving a chip (`SaveSystem/DescriptionCreator.cs` + `Saver.cs`)

`DescriptionCreator.CreateChipDescription(devChip)` snapshots the editable
circuit into a `ChipDescription`: pins ordered top→bottom then left→right,
subchips by ID, wires via index bookkeeping (`UpdateWireIndicesForDescriptionCreation`
/ `descriptionCreator_wireIndex`), size = max(saved size, computed min size
from pins+name), colour/name/displays preserved from last save.
`Saver.SaveChip` writes `Chips/<name>.json`; `SaveProjectDescription` writes
`ProjectDescription.json` (name enforced = folder name on load).

`UnsavedChangeDetector.IsEquivalentJson` compares serialized JSON ignoring
irrelevant diffs → drives "unsaved changes" prompts.

---

## 7. Save System & File Formats (`SaveSystem/`)

### 7.1 Paths (`SavePaths.cs`)

```
Editor  : <project root>/TestData/
Build   : Application.dataPath   (= <AppName>_Data folder next to the exe)
         └── Projects/<name>/ProjectDescription.json
         └── Projects/<name>/Chips/<chip>.json
         └── Deleted Projects/<name>/...
         └── AppSettings.json
```

*(Changed in this fork: builds previously used `Application.persistentDataPath`
(OS-specific AppData/`.config`); now saves live inside the app folder so the
whole build directory is portable.)*

### 7.2 JSON schema

Newtonsoft.Json, indented, custom writer (nested arrays stay inline).
Custom converters: `Vector2 {x,y}` (5 decimals), `Color {r,g,b,a}`,
`DateTime` ISO-8601.

**ProjectDescription.json** — see §3.4; `ChipCollections[].Chips` are chip
*names*; `StarredList[]` = `{Name, IsCollection}`.

**Chip .json** — see §3.4 + §4 pin layouts. Minimal example (custom chip with
one NAND, from TestData):

```json
{
  "DLSVersion": "2.1.6",
  "Name": "qwert",
  "NameLocation": 0,
  "ChipType": 0,
  "Size": {"x": 0.875, "y": 0.375},
  "Colour": {"r": 0.39, "g": 0.70, "b": 1.0, "a": 1},
  "InputPins": [{"Name":"IN","ID":1319451808,"Position":{"x":-6.87,"y":0.37},
                 "BitCount":1,"Colour":0,"ValueDisplayMode":0}],
  "OutputPins":[{"Name":"OUT","ID":1659965181,"Position":{"x":-2.45,"y":0.39},
                 "BitCount":1,"Colour":0,"ValueDisplayMode":0}],
  "SubChips":[{"Name":"NAND","ID":1586963241,"Label":"",
               "Position":{"x":-4.38,"y":0.40},
               "OutputPinColourInfo":[{"PinColour":0,"PinID":2}],
               "InternalData":null}],
  "Wires":[ ... {"SourcePinAddress":{"PinID":0,"PinOwnerID":1319451808},
                 "TargetPinAddress":{"PinID":0,"PinOwnerID":1586963241},
                 "ConnectionType":0,"ConnectedWireIndex":-1,
                 "ConnectedWireSegmentIndex":-1,
                 "Points":[{"x":0,"y":0},{"x":0,"y":0}]} ... ],
  "Displays": []
}
```

Pin-address rules for authoring files by hand:

- Boundary (dev) pin endpoint: `{PinOwnerID: <PinDescription.ID>, PinID: 0}`
- Subchip pin endpoint: `{PinOwnerID: <SubChipDescription.ID>, PinID: <pin id
  inside that chip's description>}` — builtin pin IDs: unary in=0/out=1;
  binary in=0,1/out=2; IN-x/OUT-x single pin id=0; split/merge pins numbered
  0..n-1 inputs then outputs continue.
- `ConnectionType`: 0=ToPins, 1=ToWireSource, 2=ToWireTarget.
- `InternalData`: null except ROM (19683 uints), KEY (key char), PULSE
  ([width, ticksRemaining, prevInput]), BUS ([pairID, flip]), LED ([colour]).

`Loader`/`UpgradeHelper` handle version migration; `Serializer` migrates
`BitCount`→`TritCount` and rejects non-ternary widths.

`Tools/gen_mux27.py` is a working example of programmatic chip authoring
(generated `test3/Chips/MUX-27.json`).

---

## 8. UI & Rendering (`Graphics/`)

- **Rendering**: custom immediate-mode-ish vector drawing via Seb.Vis
  (`Draw.Quad`, `Draw.Text`, `UI.*`). World space units; `GridSize=0.125`.
- **DrawSettings** (`Graphics/DrawSettings.cs`): all metrics — pin radii
  (Trit1 0.185, Trit3 0.3, Trit9 0.43), chip outline 0.05, wire 0.025,
  fonts JetbrainsMono, chip-name 0.25 / pin-label 0.2; plus `ThemeDLS` colour
  sets per state: negative=red-ish `StateLowCol`, positive=`StateHighCol`,
  zero=white `StateZeroCol`, disconnected=grey `StateDisconnectedCol`,
  per-pin-colour arrays (8 PinColours).
- **Themes**: `ThemeManager`/`ThemePalette` allow runtime UI theme editing
  (`ThemeEditorMenu`).
- **Menus** (`Graphics/UI/Menus/`): MainMenu (+`.Home`), ChipLibraryMenu
  (starred bar, collections, search, rename/delete/duplicate chips),
  ChipSaveMenu, ChipCustomizationMenu (name/colour/name-location),
  PinEditMenu, PulseEditMenu, RomEditMenu, RebindKeyChipMenu,
  PreferencesMenu (display modes, snapping, sim speed), ContextMenu
  (right-click actions per element type), SearchPopup (Ctrl+F chip search,
  recents), SimPausedUI, BottomBarUI, ViewedChipsBar, UnsavedChangesPopup.
- **World drawing**: `WorldDrawer` → `DevSceneDrawer` (chips, pins, state
  grids, names — multi-line names split on space when >6 chars),
  `WireDrawer`/`WireLayoutHelper` (auto-routing, junctions, highlighting),
  `CustomizationSceneDrawer`.
- **EditorWorkspace.cs** — chip palette UI in editor.

### Keyboard shortcuts (`KeyboardShortcuts.cs`)

- Main menu: Ctrl+N new, Ctrl+O open, Ctrl+S settings, Ctrl+Q quit
- In project: Ctrl+S save, Ctrl+L library, Ctrl+P prefs, Ctrl+N new chip,
  Ctrl+Q quit to menu, Ctrl+F search
- Editing: Ctrl+Z undo, Ctrl+Shift+Z redo, Ctrl+D duplicate (in multi-mode),
  Delete/Backspace delete, Esc cancel, Enter confirm
- Sim: Ctrl+Space pause toggle, Space (unpaused) step, Ctrl+G grid,
  Ctrl+R reset camera
- Modifiers: Ctrl = snap-to-grid hold, Alt/Shift = multi-mode (duplicate-on-
  place, add-to-selection), Shift = straight-line wires, Alt = camera pan,
  Ctrl+Shift+Alt+O = open save folder
- Tab toggles pin-name display (when pref = on-tab)

---

## 9. Interaction (`Game/Interaction/`)

- `ChipInteractionController` — placement, selection, dragging, wire drawing,
  duplication, context actions; `IDGenerator` assigns unique element IDs.
- `InteractionState` — per-frame hover/selection state (PinUnderMouse etc.).
- `UndoController` — snapshot-based undo/redo (element existence, moves, wire
  states) per DevChipInstance.
- `CameraController` — pan/zoom, remembers per-chip view state.

---

## 10. Current Fork Modifications (this working tree)

Changes made on top of upstream DLS/ternary fork:

1. **Input fallback to 0** — `PinState.FallbackDisconnectedToZero` added;
   applied to all builtin chip inputs (`Simulator.ProcessBuiltinChip`) and
   custom-chip boundary inputs (`SimChip.Sim_PropagateInputs`).
   SPECIFICATIONS §8 updated.
2. **Constant components** — `ChipType.Const_Neg1/Zero/Pos1` ("-1","0","+1"),
   `CreateConstantChip`, CONSTANTS collection, sim case driving fixed trit.
3. **MEM 1TRIT** — `ChipType.Mem_1Trit`, `CreateMem1Trit` (DATA/WE→DATA),
   InternalState init in `SimChip` + `DescriptionCreator`, WE truth table
   (+1 write / 0 hold / -1 clear), MEMORY collection, SPEC §19, README.
4. **Chip name fix** — "MEM 1TRIT" (space) so the renderer's multi-line name
   splitting keeps it inside the chip body.
5. **Self-contained saves** — `SavePaths.dataPath_Build` =
   `Application.dataPath` (was `persistentDataPath`).
6. **Open Folder button** — MainMenu project list gained a 6th button opening
   the project's save folder in the OS file browser.
7. **Build fix** — `managedStrippingLevel.Standalone` set to 0 (Disabled) in
   `ProjectSettings.asset` to avoid UnityLinker OOM on 8 GB machines.
8. **test3 project + MUX-27** — `TestData/Projects/test3/` with a generated
   27:1 ternary mux (129 gates, verified by Python netlist simulation);
   generator kept at `Tools/gen_mux27.py`.

---

## 11. Known Limitations

- Buzzer non-functional; legacy display/RAM/ROM256 chips output disconnected.
- Simulation is **zero-delay combinational within a frame** — no gate/wire
  propagation delay; sequential behavior only via Clock/Pulse/memory feedback
  resolved by frame ordering + randomized race resolution.
- Conflicting drivers on one net resolve per-trit by arrival order (later
  non-disconnected trits overwrite); no wired-AND/OR or pull-up/down.
- No waveform/history view; only current state is stored.
- Chip names are case-insensitive unique keys; renaming auto-patches parents.
- 8 GB RAM machines may struggle with Unity builds (linker OOM — mitigated by
  stripping=Disabled).

---

## 12. Dependencies & Build

- Unity **6000.6.0f1** exact (`ProjectSettings/ProjectVersion.txt`).
- Packages (`Packages/manifest.json`): Newtonsoft.Json (via Description
  serialization), Unity AI/com.unity.ai.* (assistant/inference — appear
  unused by core sim), IDE packages (Rider/VS), Linux/Windows toolchain SDKs.
- Scripting backend: **Mono** (`scriptingBackend.Standalone: 0`); managed
  stripping Disabled for Standalone.
- Build outputs observed: `Terbium-65_simulator_win_amd64.zip`,
  `Terbium-65_simulator_linux_amd64.zip`.
- No .NET SDK required; Unity's bundled toolchain compiles everything.
- First project import is slow; Library/Temp are regenerable.
