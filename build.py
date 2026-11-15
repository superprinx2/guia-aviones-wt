"""Construye GuiaAvionesWT.html (un solo archivo) y GuiaAvionesWT.apk.

Uso:  python build.py          -> HTML + APK
      python build.py --html   -> solo HTML

La app empaqueta solo textos, iconos y unas pocas fotos de armamento. Las imagenes de
los aviones (renders del juego) se cargan del wiki oficial cuando hay internet.

Firma del APK: usa build/guiawt.jks. La contrasena se lee de la variable de entorno
GUIAWT_KS_PASS o del archivo build/ks_pass.txt (ninguno de los dos se sube a git).
"""
import base64, glob, os, re, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
IMG = os.path.join(SRC, "img")
AND = os.path.join(ROOT, "android")
OUT_HTML = os.path.join(ROOT, "GuiaAvionesWT.html")
OUT_APK = os.path.join(ROOT, "GuiaAvionesWT.apk")
BUILD = os.path.join(ROOT, "build")
KEYSTORE = os.path.join(BUILD, "guiawt.jks")
SDK = os.path.expanduser(r"~\AppData\Local\Android\Sdk")
MIME = {".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml"}


def tool(name):
    """Ultima version de build-tools que tenga la herramienta."""
    for d in sorted(glob.glob(os.path.join(SDK, "build-tools", "*")), reverse=True):
        for ext in ("", ".exe", ".bat"):
            p = os.path.join(d, name + ext)
            if os.path.exists(p):
                return p
    sys.exit(f"No encuentro {name} en el Android SDK")


def android_jar():
    jars = sorted(glob.glob(os.path.join(SDK, "platforms", "android-*", "android.jar")))
    if not jars:
        sys.exit("No encuentro platforms/android-*/android.jar en el Android SDK")
    return jars[-1]


def ks_pass():
    p = os.environ.get("GUIAWT_KS_PASS")
    f = os.path.join(BUILD, "ks_pass.txt")
    if not p and os.path.exists(f):
        p = open(f, encoding="utf-8").read().strip()
    if not p:
        sys.exit("Falta la contrasena del keystore: define GUIAWT_KS_PASS o crea build/ks_pass.txt")
    return p


def data_uri(name):
    for ext, mime in MIME.items():
        p = os.path.join(IMG, name + ext)
        if os.path.exists(p):
            with open(p, "rb") as f:
                return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    print("  (sin imagen)", name)
    return ""


def build_html():
    html = open(os.path.join(SRC, "app.html"), encoding="utf-8").read()
    cache = {}
    html = re.sub(r"%%IMG:(\w+)%%", lambda m: cache.setdefault(m[1], data_uri(m[1])), html)
    creds_path = os.path.join(SRC, "credits.json")
    creds = open(creds_path, encoding="utf-8").read() if os.path.exists(creds_path) else "{}"
    html = html.replace("%%CREDITS%%", creds)
    html = html.replace("%%CATALOG%%", open(os.path.join(SRC, "catalog.json"), encoding="utf-8").read())
    html = html.replace("%%DETAILS%%", open(os.path.join(SRC, "details.json"), encoding="utf-8").read())
    html = html.replace("%%ORIGBLK%%", open(os.path.join(SRC, "orig.blk"), encoding="utf-8").read())
    html = html.replace("%%THREE%%", open(os.path.join(SRC, "three.min.js"), encoding="utf-8").read())
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"HTML: {OUT_HTML} ({len(html) / 1024:.0f} KB)")
    return html


def run(*cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def build_apk(html):
    jar = android_jar()
    work = os.path.join(BUILD, "apk")
    shutil.rmtree(work, ignore_errors=True)
    for d in ("res", "classes", "dex"):
        os.makedirs(os.path.join(work, d))
    # 1) recursos + manifest
    flat = os.path.join(work, "res.zip")
    run(tool("aapt2"), "compile", "--dir", os.path.join(AND, "res"), "-o", flat)
    base = os.path.join(work, "base.apk")
    run(tool("aapt2"), "link", "-o", base, "-I", jar, "--manifest", os.path.join(AND, "AndroidManifest.xml"), flat)
    # 2) codigo Java -> dex
    srcs = glob.glob(os.path.join(AND, "src", "**", "*.java"), recursive=True)
    run("javac", "-source", "8", "-target", "8", "-nowarn", "-Xlint:-options", "-bootclasspath", jar,
        "-d", os.path.join(work, "classes"), *srcs)
    classes = glob.glob(os.path.join(work, "classes", "**", "*.class"), recursive=True)
    run(tool("d8"), "--release", "--min-api", "21", "--lib", jar, "--output", os.path.join(work, "dex"), *classes)
    # 3) empaquetar
    unsigned = os.path.join(work, "unsigned.apk")
    with zipfile.ZipFile(base) as zin, zipfile.ZipFile(unsigned, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            zout.writestr(it, zin.read(it.filename), compress_type=it.compress_type)
        zout.write(os.path.join(work, "dex", "classes.dex"), "classes.dex")
        zout.writestr("assets/index.html", html.encode("utf-8"))
    aligned = os.path.join(work, "aligned.apk")
    run(tool("zipalign"), "-p", "-f", "4", unsigned, aligned)
    pw = ks_pass()
    run(tool("apksigner"), "sign", "--ks", KEYSTORE, "--ks-pass", "pass:" + pw, "--out", OUT_APK, aligned)
    run(tool("apksigner"), "verify", OUT_APK)
    print(f"APK: {OUT_APK} ({os.path.getsize(OUT_APK) / 1024:.0f} KB)")


if __name__ == "__main__":
    h = build_html()
    if "--html" not in sys.argv:
        build_apk(h)
