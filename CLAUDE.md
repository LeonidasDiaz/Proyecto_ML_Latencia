# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este proyecto

Proyecto de investigación terminado (Universidad Mundo Maya, junio de 2026). Evalúa si Random Forest y XGBoost pueden predecir la latencia HTTP de un servidor con 30 s de antelación, usando como variables el consumo de CPU y RAM. **La hipótesis se refutó:** el R² salió negativo en ambos modelos. El autor y el código están en español. Escribe en español los comentarios, los mensajes y la documentación.

Documentación de contexto. Léela antes de tocar el análisis o las conclusiones:
- `docs/Leonidas_Diaz_Flores.pdf`: documento final de la investigación y fuente primaria. Ante una contradicción, manda sobre docs/CONTEXTO_INVESTIGACION.md, que es un resumen. Está en `.gitignore` a propósito, porque el autor debe revisar los datos personales antes de publicarlo. No lo commitees ni lo saques del `.gitignore`.
- [docs/CONTEXTO_INVESTIGACION.md](docs/CONTEXTO_INVESTIGACION.md) resume el documento final de la investigación. Trae los resultados oficiales, el entorno experimental y una tabla de **discrepancias** entre el documento, el código y los datos. Si una cifra del notebook o de un README no coincide con esta tabla, revisa la discrepancia antes de cambiar nada.
- [docs/BITACORA.md](docs/BITACORA.md) reconstruye la historia del proyecto a partir de git y de los datos. Se escribió **antes** que docs/CONTEXTO_INVESTIGACION.md, así que varias de sus preguntas abiertas (P1, P3, P7 y P12) ya tienen respuesta ahí.
- [docs/AUDITORIA.md](docs/AUDITORIA.md): auditoría de código del 2026-11-01. Los códigos A1–A4, M1–M8 y B1–B10 que aparecen en los otros documentos remiten a ella.

Convención de ambos documentos: no inventar justificaciones. Lo que no esté documentado se marca como "valor elegido sin justificación documentada" o como "Deducido", nunca como un hecho.

## Arquitectura: dos entornos

El experimento se ejecuta en dos máquinas distintas. Ningún script se conecta directamente con los demás: el único enlace entre ellos es el archivo CSV.

1. **VM con Ubuntu Server** (recolección). Allí corren a la vez tres procesos, conectados por SSH:
   - El servidor medido: `python3 -m http.server 8080`. No está en el repo.
   - [src/recolector.py](src/recolector.py): cada 5 s lee CPU y RAM con `psutil` y mide un `GET http://127.0.0.1:8080/`. Agrega una fila al CSV y se detiene a las 5000 filas.
   - [src/estresador.sh](src/estresador.sh): repite ciclos de 20 min con 10 min de reposo, 5 min de `stress-ng` y 5 min de recuperación. Requiere `stress-ng`. [.gitattributes](.gitattributes) fuerza saltos de línea LF en los `.sh` para que funcionen en Linux.
2. **Windows con `venv/`** (análisis). El CSV llega por `scp` a `data/raw/`. [notebooks/analisis.ipynb](notebooks/analisis.ipynb) contiene **todo** el pipeline: creación del objetivo con `shift(-6)` (30 s), split temporal 80/20, entrenamiento de RF y XGB, clasificación de picos con umbral media + 2σ y comparación de horizontes. [src/entrenamiento.py](src/entrenamiento.py) está vacío.

## Comandos

En la VM, ejecutar desde `src/`, porque la ruta del CSV es relativa (`../data/raw/`):
```bash
cd src
python3 recolector.py      # terminal 1
bash estresador.sh         # terminal 2
```

En Windows, para el análisis:
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```
El notebook se ejecuta desde VS Code con el kernel `venv`. `nbconvert` no está instalado, así que no se puede ejecutar por línea de comandos sin agregarlo antes.

No hay tests, linter ni build.

## Trampas que no se ven en el código

- **Dos datasets que no se pueden comparar.** `data/raw/registro_rendimiento.csv` (dataset 1, 10 000 filas) se midió con **ping ICMP** al loopback, usando una versión anterior de `recolector.py`; verlo con `git show bd720dc:src/recolector.py`. Se descartó. El dataset oficial es `registro_rendimiento2.csv` (HTTP, 5000 filas). Ese archivo aún no está commiteado y es el que lee el notebook.
- **El recolector sobrescribe** el CSV al arrancar (lo abre en modo `'w'`), y siempre con el nombre `registro_rendimiento.csv`.
- **`Latencia_ms == 0.0` significa error o timeout,** no una latencia real. Los datasets actuales no tienen ningún 0.0.
- **`Timestamp` está en el reloj de la VM, que es UTC.** La hora local del autor es UTC−6.
- **`requirements.txt`** está codificado en UTF-16 (sale de `pip freeze` en PowerShell) y le falta `requests`. Solo cubre el entorno de análisis en Windows. En la VM se usaron los paquetes del sistema `python3-requests` y `python3-psutil`.
- **Los resultados del notebook son los que cita el documento final:** R² de −0.23 (RF) y −0.71 (XGB), y recall de picos de 0.27. Si vuelves a ejecutar el notebook y cambian, avisa antes de reemplazarlos.
- **21 vs 23 ciclos no es un error.** El documento reporta 21 ciclos y el código tiene `TOTAL_CICLOS=23`. El recolector se detuvo a las 5000 muestras, antes de los ciclos 22 y 23, y en el dataset 2 se ven exactamente 21 episodios de estrés. No "corrijas" ninguno de los dos valores.
