"""Genera src/catalog.json compacto a partir de wiki/prem.json y verifica las imagenes del wiki."""
import concurrent.futures as cf, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "build")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "src", "catalog.json")
d = json.load(open(os.path.join(D, "wiki", "prem.json"), encoding="utf-8"))
s = [x for x in d if x["ge"] or x["store"]]
ROLE = {"fighter": "f", "assault": "a", "bomber": "b"}
NAT = ["usa", "germany", "ussr", "britain", "japan", "china", "italy", "france", "sweden", "israel"]
RK = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def head(u):
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        return urllib.request.urlopen(req, timeout=30).status == 200
    except Exception:
        return False


with cf.ThreadPoolExecutor(12) as ex:
    img = list(ex.map(lambda x: head(f"https://static.encyclopedia.warthunder.com/images/{x['id']}.png"), s))
    slot = list(ex.map(lambda x: head(f"https://static.encyclopedia.warthunder.com/slots/{x['id']}.png"), s))
print("sin imagen:", [x["id"] for x, ok in zip(s, img) if not ok], "sin slot:", [x["id"] for x, ok in zip(s, slot) if not ok])

cat = []
for x in s:
    w = set(x["w"])
    if x["ico"] == "bomber":
        w.add("bomb")
    e = [x["id"], x["n"], NAT.index(x["c"]), RK.index(x["rk"]) + 1, x["br"][1] if len(x["br"]) > 1 else x["br"][0],
         ROLE.get(x["ico"], "f"), x["ge"] or 0, int(x["sid"]) if x["store"] and x["sid"] else 0,
         int(x["spd"].replace(",", "")) if x["spd"] else 0, int(x["crew"] or 1), x["eng"] or "",
         " · ".join(x["guns"]), "".join({"aam": "m", "agm": "g", "bomb": "b", "rkt": "r", "tor": "t"}[k] for k in sorted(w)), " · ".join(x["aamn"])]
    cat.append(e)
cat.sort(key=lambda e: (e[2], e[3], float(e[4])))
json.dump(cat, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(cat), os.path.getsize(OUT), "bytes")

