import json

P = r"C:/Users/HP/AppData/Local/hermes/work_repos/fieldcore/tests/data/informed_adversarial.json"
d = json.load(open(P, encoding="utf-8"))
for i, r in enumerate(d):
    print("%2d g%s | %s" % (i, r["goal"], r["span"]))
