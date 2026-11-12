import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_cobalt

src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "test_compare2.py")).read()
m = re.search(r'DEMO2 = """(.*?)"""', src, re.S)
gen_cobalt.main(m.group(1),
                os.path.join("..", "..", "TestData", "Projects", "Cobalt2"),
                "Cobalt2")
