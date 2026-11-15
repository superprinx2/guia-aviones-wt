"""Extrae datos detallados de cada avion del catalogo desde las paginas del wiki ya descargadas
(build/wiki/u/<id>.html, las baja tools/scrape_wiki.py) y genera build/wiki/details.json.

Por avion: rendimiento, limites, flaps/aerofreno, sensores (radar, RWR, IRST...), canones,
y la matriz arma x slot de pilones (que arma cabe en que slot) con pesos y limites de carga.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "build", "wiki")


def txt(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def num(s):
    m = re.search(r"-?[\d,]+(?:\.\d+)?", s or "")
    return float(m[0].replace(",", "")) if m else None


def popover_fields(h):
    """Convierte el HTML de un popover (chars-line / chars-subline) en lista de (clave, valor)."""
    out = []
    for m in re.finditer(r'<div class="game-unit_chars-(?:line|subline)">\s*<div[^>]*>(.*?)</div>\s*<div class="game-unit_chars-value[^"]*"[^>]*>(.*?)</div>', h, re.S):
        k, v = txt(m[1]), m[2]
        if "check-circle-fill" in v:
            val = True if not txt(v) else "+" + txt(v).lstrip("+ ").strip()
        elif "x-circle" in v:
            val = False
        else:
            val = txt(v)
        out.append((k, val))
    return out


def chars(t):
    """Pares cabecera/valor de los bloques de caracteristicas (valor RB mejorado si hay varios)."""
    d = {}
    for m in re.finditer(r'<span class="game-unit_chars-header">(.*?)</span>\s*<span class="game-unit_chars-value">(.*?)</span>\s*</div>', t, re.S):
        k = txt(m[1])
        v = m[2]
        r = re.search(r'show-char-rb-mod-ref[^>]*>([^<]*)<', v)
        d.setdefault(k, txt(r[1]) + " " + txt(re.sub(r"<span[^>]*>[^<]*</span>", "", v)) if r else txt(v))
    return d


def wtype(name):
    n = name.lower()
    for k, p in [("aam", "air-to-air missile"), ("arm", "anti-radiation"), ("gbomb", "guided bomb"), ("pod", "targeting pod"),
                 ("gpod", "gun pod|cannon pod|machine gun pod|gunpod"), ("tank", "fuel tank|drop tank"), ("tor", "torpedo"),
                 ("agm", "missile"), ("rkt", "rocket"), ("mine", "mine"), ("bomb", "bomb|munition|napalm")]:
        if re.search(p, n):
            return k
    if re.search(r"\bcannon|machine gun|\bmm\b", n):
        return "gpod"
    return "other"


def parse(uid, WD, WI):
    t = open(os.path.join(W, "u", uid + ".html"), encoding="utf-8").read()
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", t)
    r = {}
    c = chars(t)
    g = lambda k: c.get(k)
    r["p"] = {k: v for k, v in {
        "spd": num(next((v for k, v in c.items() if k.startswith("Max speed")), None)),
        "spdAlt": num(next((k for k in c if k.startswith("Max speed")), "")),
        "climb": num(g("Rate of Climb")), "turn": num(g("Turn time")), "alt": num(g("Max altitude")),
        "run": num(g("Takeoff Run")), "len": num(g("Length")), "span": num(g("Wingspan")),
        "wl": num(g("Wing Loading")), "w": num(g("Base weight")), "ias": num(g("Max Speed Limit (IAS)")),
        "mach": num(g("Mach Number Limit")), "flap": g("Flap Speed Limit (IAS)"), "gear": num(g("Gear Speed Limit (IAS)")),
    }.items() if v is not None}
    gl = g("G limit")
    if gl:
        m = re.findall(r"-?\d+(?:\.\d+)?", gl)
        if len(m) >= 2:
            r["p"]["g"] = [float(m[0]), float(m[1])]
    # flaps / aerofreno
    i = t.find("Landing<br>flaps")
    if i >= 0:
        r["fl"] = [x == "check-circle-fill" for x in re.findall(r"bi-(check-circle-fill|x-circle)", t[i:i + 1500])][:4]
    # popovers de caracteristicas (radar, RWR, motor...)
    feats, radar, rwr, eng = [], None, None, {}
    for m in re.finditer(r'class="game-unit_feature"[^>]*data-feature-popover="([^"]*)"', t):
        h = html.unescape(m[1])
        title = txt((re.search(r"<span>(.*?)</span>", h) or [None, ""])[1])
        feats.append(title)
        f = dict(popover_fields(h))
        if title in ("Radar/Optical Detection", "Radar", "Optical Detection"):
            radar = {"m": f.get("Model"), "radar": bool(f.get("Radar")), "band": f.get("Band"), "tws": f.get("TWS"),
                     "iff": f.get("IFF"), "opt": f.get("Optical Detection"), "s": f.get("Search"), "t": f.get("Track")}
            radar = {k: v for k, v in radar.items() if v not in (None, "")}
        elif title in ("RWR", "Radar Warning System"):
            rwr = {k: v for k, v in {"m": f.get("Model"), "rng": f.get("Range"), "launch": f.get("Launch detection"),
                                     "track": f.get("Tracking detection"), "iff": f.get("IFF")}.items() if v not in (None, "")}
    for m in re.finditer(r'data-feature-popover="([^"]*)"', t):
        h = html.unescape(m[1])
        f = popover_fields(h)
        keys = [k for k, _ in f]
        if "Type" in keys and any(k.startswith("Engine") for k in keys) or any(k in ("Maximum", "Afterburner", "WEP") for k in keys) and "Type" in keys:
            d = dict(f)
            eng = {"type": d.get("Type"), "max": d.get("Maximum"), "ab": d.get("Afterburner") or d.get("WEP")}
            break
    r["ft"] = [x for x in feats if x]
    if radar:
        r["radar"] = radar
    if rwr:
        r["rwr"] = rwr
    if eng:
        r["eng"] = {k: v for k, v in eng.items() if v}
    # canones ofensivos y defensivos
    x = txt(t)
    def gun_block(label, stop):
        i = x.find(label)
        if i < 0:
            return []
        seg = x[i:x.find(stop, i + 10) if x.find(stop, i + 10) > 0 else i + 1500][:1500]
        out = []
        for m in re.finditer(r"((?:\d+ x )?\d+(?:\.\d+)? mm [^ ]+(?: [^ ]+)? (?:cannon|machine gun)s?)(?: Ammunition ([\d,]+) rounds)?(?: Fire rate ([\d,]+) shots/min)?", seg):
            out.append([m[1], int(m[2].replace(",", "")) if m[2] else 0, int(m[3].replace(",", "")) if m[3] else 0])
        return out
    r["guns"] = gun_block("Offensive armament", "Suspended armament")
    dg = gun_block("Defensive armament", "Suspended armament")
    if dg:
        r["dguns"] = dg
    # carga externa
    i = x.find("Suspended armament")
    seg = x[i:i + 400] if i >= 0 else ""
    mw = re.search(r"Max weight ([\d,]+) kg", seg)
    if mw:
        r["maxW"] = num(mw[1])
    mm = re.search(r"Maximum ([\d,]+) kg", seg)
    if mm:
        r["wingMax"] = num(mm[1])
    md = re.search(r"Max\. difference ([\d,]+) kg", seg)
    if md:
        r["maxDiff"] = num(md[1])
    # matriz arma x slot
    m = re.search(r'<table class="game-unit_slot-list[\s\S]*?</table>', t)
    if m:
        tb = m[0]
        rows = re.findall(r"<tr>([\s\S]*?)</tr>", tb)
        hdr = re.search(r'colspan="(\d+)"', tb)
        n = int(hdr[1]) if hdr else 0
        r["n"] = n
        first = next((rw for rw in rows if "border-top" in rw), "")
        cols = re.findall(r"border-top:\s*3px solid ([^\";]+)", first)
        r["side"] = "".join("l" if cc.strip() == "red" else "c" if cc.strip() == "gray" else "r" for cc in cols)
        wl = []
        for rw in rows:
            tds = re.findall(r"<td[^>]*>([\s\S]*?)</td>", rw)
            if len(tds) < 3:
                continue
            pm = re.search(r'data-feature-popover="([^"]*)"', tds[0])
            name = txt(re.sub(r'data-feature-popover="[^"]*"', "", tds[0])).replace("\xa0", " ")
            weight = num(txt(tds[1]))
            cells = tds[2:]
            mask = [i for i, cc in enumerate(cells) if "<img" in cc]
            if not mask:
                continue
            icon = (re.search(r"gui_skin/([\w\-]+)\.png", "".join(cells)) or [None, ""])[1]
            info = {}
            if pm:
                for k, v in popover_fields(html.unescape(pm[1])):
                    info[k] = v
            key = name + "|" + str(weight)
            if key not in WI:
                ch = {}
                for k, kk in [("Guidance", "gd"), ("Aspect", "asp"), ("Lock range in rear-aspect", "lr"), ("Lock range in all-aspect", "la"),
                              ("Launch range", "rng"), ("Maximum speed", "spd"), ("Maximum overload", "g"), ("Missile guidance time", "time"),
                              ("Explosive Mass", "ex"), ("TNT equivalent", "tnt"), ("Armor penetration", "pen")]:
                    if info.get(k) not in (None, "", True, False):
                        ch[kk] = info[k]
                    elif info.get(k) is True:
                        ch[kk] = True
                for k in ("IRCCM", "Datalink", "Fire-and-forget", "Proximity fuse"):
                    if k in info:
                        ch[k[:3].lower()] = bool(info[k])
                WI[key] = len(WD)
                WD.append([name, weight, icon, wtype(name), ch])
            wl.append([WI[key], sum(1 << i for i in mask)])
        r["wp"] = wl
    return r


if __name__ == "__main__":
    ids = json.loads(sys.argv[1]) if len(sys.argv) > 1 else None
    prem = json.load(open(os.path.join(W, "prem.json"), encoding="utf-8"))
    ids = ids or [p["id"] for p in prem if p["ge"] or p["store"]]
    WD, WI, out = [], {}, {}
    for uid in ids:
        out[uid] = parse(uid, WD, WI)
    json.dump({"weapons": WD, "planes": out}, open(os.path.join(W, "details.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(len(out), "aviones,", len(WD), "armas distintas")
