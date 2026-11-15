# Guía Aviones WT

Guía no oficial de War Thunder para Android, hecha por fans. **Eliges tu avión y toda la guía se adapta a él.**

## Lo principal

- **Editor de controles:** importa el `.blk` que exportas desde War Thunder, mira qué tecla tiene cada función de *tu* avión (y cuáles no tienen tecla o están repetidas), cámbialas y exporta el archivo para cargarlo de nuevo en el juego.
- **34 aviones modernos premium**: rango V o superior, con radar de búsqueda, que se compran con águilas doradas o en paquete. Se eligen desde la pantalla inicial, con filtros.
- **Guía por avión**, armada con los datos reales del wiki oficial:
  - **Radar**: pantalla al estilo del juego con los modos que tiene ese radar (búsqueda, TWS, lock, ACM) y tus teclas para cada uno.
  - **IRST** (sensor de calor) en los aviones que lo tienen.
  - **Armamento** con los íconos del juego, alcance, velocidad y cómo usar cada arma.
  - **Pilones**: cada slot solo acepta las armas que el juego permite en ese slot, con control de peso total y por ala.
  - **Setups** listos (aire-aire, solo IR, mixto, ataque, antiradar, bombas) que siempre respetan los slots y los pesos.
  - **Maniobras**, **defensa** y **ataque a tierra** según las características del avión.
- El **Su-30MKK** mantiene además su guía detallada: modelo 3D, panel de radar y tácticas.

## Descargar

Descarga el APK desde **[Releases](../../releases/latest)** e instálalo en tu celular. Android te pedirá permitir la instalación de "fuentes desconocidas".

## Imágenes

Los renders de los aviones y los íconos de armas son del [wiki oficial de War Thunder](https://wiki.warthunder.com). **No van dentro de la app**: se cargan por internet, por eso el APK pesa unos 300 KB. Sin conexión verás siluetas.

## Compilar

Requisitos: Python 3, JDK 17 y el Android SDK (build-tools y `platforms/android-*`).

```bash
python build.py          # genera GuiaAvionesWT.html y GuiaAvionesWT.apk
python build.py --html   # solo el HTML (para probar en el navegador)
```

Para firmar el APK hace falta `build/guiawt.jks` y su contraseña en la variable `GUIAWT_KS_PASS` o en `build/ks_pass.txt`. Ninguno de los dos está en el repositorio.

### Actualizar los datos de los aviones

```bash
python tools/scrape_wiki.py --refresh   # descarga las páginas del wiki
python tools/scrape_details.py          # slots de pilones, radar, sensores, rendimiento
python tools/make_catalog.py            # src/catalog.json (filtro: premium, rango V+, con radar)
python tools/make_details.py            # src/details.json
```

## Estructura

| Ruta | Qué es |
|---|---|
| `src/app.html` | La app completa (HTML + CSS + JS, una sola página) |
| `src/catalog.json` | Catálogo de aviones (generado) |
| `src/details.json` | Datos por avión: slots, armas, radar, rendimiento (generado) |
| `src/orig.blk` | Archivo de controles base |
| `android/` | Contenedor Android (WebView) |
| `tools/` | Scripts para actualizar los datos desde el wiki |

## Aviso

War Thunder es marca de Gaijin Entertainment. Esta app no está afiliada ni respaldada por Gaijin. Los renders, íconos y datos de los aviones son © Gaijin Entertainment y se muestran desde su wiki oficial. Los precios son orientativos y pueden cambiar con actualizaciones y ofertas.
