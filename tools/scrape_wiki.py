"""Extrae del wiki de WT los aviones premium comprables con aguilas doradas (GE) o en paquete (tienda)."""
import concurrent.futures as cf, html, json, re, sys, urllib.request, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "build", "wiki")
os.makedirs(D, exist_ok=True)
AVP = os.path.join(D, "aviation.html")
if not os.path.exists(AVP) or "--refresh" in sys.argv:
    urllib.request.urlretrieve("https://wiki.warthunder.com/aviation", AVP)
av = open(AVP, encoding="utf-8").read()

# nacion por bloque de arbol: buscar el pais en cada seccion
ids = re.findall(r'wt-tree_item--prem" data-unit-id="([^"]+)"', av)
ids = list(dict.fromkeys(ids))

UA = {"User-Agent": "Mozilla/5.0 (fan guide data builder)"}


def txt(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def fetch(uid):
    p = os.path.join(D, "u", uid + ".html")
    if os.path.exists(p) and "--refresh" not in sys.argv:
        return open(p, encoding="utf-8").read()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    req = urllib.request.Request("https://wiki.warthunder.com/unit/" + uid, headers=UA)
    t = urllib.request.urlopen(req, timeout=40).read().decode("utf-8")
    open(p, "w", encoding="utf-8").write(t)
    return t


def info(t, title):
    m = re.search(r'<div class="game-unit_card-info_value">([\s\S]{0,900}?)</div>\s*<div class="game-unit_card-info_title">' + title + "<", t)
    return m


def parse(uid):
    t = fetch(uid)
    r = {"id": uid}
    m = None
    name = ""
    if not name:
        m = re.search(r"<title>(.*?) \((?:[^()]*)\) \|", t) or re.search(r"<title>(.*?) \|", t)
        name = html.unescape(m[1]).strip() if m else uid
    r["n"] = name.replace("â—", "").replace("â—Ž", "").replace("â€‚", " ").replace("\xa0", " ").strip()
    m = re.search(r'game-unit_rank[^>]*>([\s\S]*?)</div>', t)
    rk = re.search(r">\s*([IVX]+)\s*<", t[t.find("game-unit_card-info"):]) if "game-unit_card-info" in t else None
    m = re.search(r'([IVX]+)\s*</div>\s*<div class="game-unit_card-info_title">Rank', t)
    r["rk"] = m[1] if m else (rk[1] if rk else "")
    # BR: primera fila AB RB SB
    m = re.search(r"Battle rating", t)
    seg = txt(t[t.find("game-unit_br"):t.find("Battle rating")]) if "game-unit_br" in t else ""
    nums = re.findall(r"\b(\d{1,2}\.\d)\b", seg)
    r["br"] = nums[:3]
    m = re.search(r'country_svg/country_(\w+)\.svg', t)
    r["c"] = m[1] if m else ""
    m = re.search(r'class_icon/(\w+)\.svg[\s\S]{0,300}?text-truncate">([^<]+)</div>\s*</div>\s*<div class="game-unit_card-info_title">Main role', t)
    r["role"] = m[2].strip() if m else ""
    r["ico"] = m[1] if m else ""
    m = re.search(r"<div>([\d,\s]+)</div>\s*<div>\s*<img[^>]*item_type_eagles", t)
    r["ge"] = int(re.sub(r"\D", "", m[1])) if m else None
    r["store"] = "game-unit_link--store" in t
    r["market"] = "game-unit_link--market" in t
    m = re.search(r'game-unit_link--store" href="([^"]+)"', t)
    sid = re.search(r"[?&]id=(\d+)", html.unescape(m[1])) if m else None
    r["sid"] = sid[1] if sid else None
    body = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", t)
    x = txt(body)
    g = lambda p: (re.search(p, x) or [None, None])[1]
    r["spd"] = g(r"Max speed at [\d,]+ m ([\d,]+) ")
    r["alt"] = g(r"Max speed at ([\d,]+) m")
    r["crew"] = g(r"Crew (\d+) person")
    r["eng"] = g(r"Engine (.{2,40}?) (?:Length|Wingspan|Engine|Weight|Fuel)")
    r["guns"] = list(dict.fromkeys(re.findall(r"((?:\d+ x )?\d+(?:\.\d+)? mm [^ ]+(?: [^ ]+)? (?:cannon|machine gun)s?)", x[x.find("Offensive armament"):x.find("Offensive armament") + 500])))[:3] if "Offensive armament" in x else []
    r["def"] = "Defensive armament" in x
    w = x[x.find("List of available weapons"):] if "List of available weapons" in x else ""
    r["w"] = sorted({k for k, p in [("aam", "air-to-air missile"), ("agm", r"guided bomb|anti-radiation missile|anti-ship missile|(?<!air-to-air )missiles \d"), ("bomb", " bomb"), ("rkt", "rockets"), ("tor", "torpedo")] if re.search(p, w[:6000])})
    r["aamn"] = list(dict.fromkeys(a.replace("Slot ", "") for a in re.findall(r"([A-Z][\w\-\.]+(?: [\w\-\.]+)?) air-to-air missiles", w[:6000])))[:4]
    return r


out = []
with cf.ThreadPoolExecutor(8) as ex:
    for r in ex.map(parse, ids):
        out.append(r)
        print(r["id"], r["c"], r["rk"], r["br"], r["role"], r["ge"], "STORE" if r["store"] else "", "MKT" if r["market"] else "", file=sys.stderr)
json.dump(out, open(os.path.join(D, "prem.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(out))


