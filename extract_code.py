import json, re, sys
data = json.load(open(sys.argv[1]))
texts = []
def walk(x):
    if isinstance(x, str): texts.append(x)
    elif isinstance(x, dict): [walk(v) for v in x.values()]
    elif isinstance(x, list): [walk(v) for v in x]
walk(data)
found = [t for t in texts if "setup" in t and "draw" in t]
if not found: sys.exit("No p5.js code found in " + sys.argv[1])
text = max(found, key=len)
m = re.search(r"```(?:javascript|js)?\s*\n(.*?)```", text, re.S)
open(sys.argv[2], "w").write((m.group(1) if m else text).strip() + "\n")
print("Wrote", sys.argv[2])
