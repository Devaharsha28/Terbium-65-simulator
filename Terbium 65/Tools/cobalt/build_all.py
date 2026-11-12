import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chips, blocks, blocks2

chips.REGISTRY.clear()
for b in blocks.BUILDERS + blocks2.BUILDERS2:
    try:
        name = b()
        d = chips.REGISTRY[name.lower()]
        print("%s: %d subchips, %d wires, %d in / %d out" % (
            name, len(d["SubChips"]), len(d["Wires"]),
            len(d["InputPins"]), len(d["OutputPins"])))
    except Exception:
        import traceback
        traceback.print_exc()
        break
