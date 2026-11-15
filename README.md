# Guía Aviones WT

Guía no oficial de War Thunder para Android, hecha por fans:

- **Guía completa del Su-30MKK**: modelo 3D, armamento aire-aire y aire-tierra, setups de pilones, radar, combate BVR y editor de controles (`.blk`).
- **Catálogo de 178 aviones premium** que se pueden comprar hoy, con filtros por nación, rango y tipo:
  - **148 con águilas doradas** (con su precio base)
  - **44 en paquetes** de la tienda de Gaijin (con enlace al paquete)
  - Cada avión tiene una ficha con BR, velocidad, motor, armamento y la opción "Lo tengo" para armar tu propio hangar.

## Descargar

Descarga el APK desde **[Releases](../../releases/latest)** e instálalo en tu celular. Android te pedirá permitir la instalación de "fuentes desconocidas".

## Imágenes

Las imágenes de los aviones son los renders del juego del [wiki oficial de War Thunder](https://wiki.warthunder.com). **No van dentro de la app**: se cargan por internet cuando abres cada avión, así la app pesa menos de 1 MB. Sin conexión verás una silueta.

## Compilar

Requisitos: Python 3, JDK 17 y el Android SDK (build-tools y `platforms/android-*`).

```bash
python build.py          # genera GuiaAvionesWT.html y GuiaAvionesWT.apk
python build.py --html   # solo el HTML (para probar en el navegador)
```

Para firmar el APK hace falta `build/guiawt.jks` y su contraseña en la variable `GUIAWT_KS_PASS` o en `build/ks_pass.txt`. Ninguno de los dos está en el repositorio.

### Actualizar el catálogo

```bash
python tools/scrape_wiki.py --refresh   # descarga los datos del wiki
python tools/make_catalog.py            # regenera src/catalog.json
```

## Estructura

| Ruta | Qué es |
|---|---|
| `src/app.html` | La app completa (HTML + CSS + JS, una sola página) |
| `src/catalog.json` | Catálogo de aviones premium (generado) |
| `src/img/` | Fotos de armamento y plano del Su-30 (Wikimedia Commons) |
| `android/` | Contenedor Android (WebView) |
| `tools/` | Scripts para actualizar el catálogo desde el wiki |

## Aviso

War Thunder es marca de Gaijin Entertainment. Esta app no está afiliada ni respaldada por Gaijin. Los renders y datos de los aviones son © Gaijin Entertainment y se muestran desde su wiki oficial. Los precios son orientativos y pueden cambiar con actualizaciones y ofertas.
