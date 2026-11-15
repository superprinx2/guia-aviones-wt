"""Genera src/details.json (compacto) a partir de build/wiki/details.json (tools/scrape_details.py)."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "build", "wiki", "details.json"), encoding="utf-8"))
FT = {"Drogue parachute": "chute", "Flares/Chaff": "cm", "Chaff": "cm", "Infrared countermeasures": "ircm",
      "Radar Warning System": "rwr", "Ballistic Computer": "bc", "Helmet-mounted display": "hmd",
      "Night vision device": "nvd", "Thermal imager": "ti", "Voice warning system": "voice", "Fuel dumping": "fd",
      "Arrestor gear": "hook", "Vertical Take-Off and Landing": "vtol", "Swing wing": "swing", "Boosters": "boost"}
CAT = {r[0] for r in json.load(open(os.path.join(ROOT, "src", "catalog.json"), encoding="utf-8"))}
used = set()
for k in CAT:
    used.update(w for w, _ in d["planes"][k].get("wp", []))
remap = {old: new for new, old in enumerate(sorted(used))}
d["weapons"] = [d["weapons"][i] for i in sorted(used)]
for k in CAT:
    d["planes"][k]["wp"] = [[remap[w], m] for w, m in d["planes"][k].get("wp", [])]
P = {}
for k, p in d["planes"].items():
    if k not in CAT:
        continue
    q = dict(p)
    q["ft"] = sorted({FT[f] for f in p.get("ft", []) if f in FT})
    if not q.get("wp"):
        for x in ("wp", "n", "side"):
            q.pop(x, None)
    P[k] = q
out = {"w": d["weapons"], "p": P}
path = os.path.join(ROOT, "src", "details.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(path, os.path.getsize(path), "bytes")
