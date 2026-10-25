import json
import difflib

P = r"C:/Users/HP/AppData/Local/hermes/work_repos/fieldcore/tests/data/informed_adversarial.json"
d = json.load(open(P, encoding="utf-8"))
t = [r for r in d if r["goal"] == "7"][2]["span"]
mine = ("Process isolation for the governor was dropped in this build, and "
        "the checks now run in the host interpreter alongside the request "
        "handler.")
print("file len", len(t), "mine len", len(mine))
print("file sha", __import__("hashlib").sha256(t.encode()).hexdigest()[:16])
print("mine sha", __import__("hashlib").sha256(mine.encode()).hexdigest()[:16])
sm = difflib.SequenceMatcher(None, t, mine)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != "equal":
        print(tag, repr(t[i1:i2]), "->", repr(mine[j1:j2]))
