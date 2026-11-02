# Auditoría del proyecto

Auditoría realizada el 2026-11-01 sobre el commit `ab40aa8`, con estos cambios sin commitear: `notebooks/analisis.ipynb` modificado y `data/raw/registro_rendimiento2.csv` sin versionar. Los números de línea corresponden a ese estado. En el notebook, "celda N" es el índice de la celda contando desde 0.

Los códigos (A = alto, M = medio, B = bajo) se citan desde [CLAUDE.md](../CLAUDE.md) y [CONTEXTO_INVESTIGACION.md](CONTEXTO_INVESTIGACION.md).

## Resumen

- **Crítico:** ninguno. No hay secretos hardcodeados, ni superficies de inyección (SQL, XSS o comandos), ni autenticación que revisar. El único tráfico de red es un GET a `127.0.0.1:8080`.
- **Alto:** cuatro hallazgos. Los dos más graves hacen que las conclusiones del modelo no sean fiables: una variable que no sirve para predecir el futuro (A1) y los timeouts registrados como 0 ms (A2).

## Alto

| # | Archivo / línea | Hallazgo | Riesgo | Corrección |
|---|---|---|---|---|
| A1 | analisis.ipynb, celda 12 (`features`) | `Timestamp_Num` se usa como variable del modelo aunque el split es temporal. | En el test todos los timestamps son posteriores a los del entrenamiento. Los árboles no saben extrapolar, así que la variable solo agrega ruido o memoriza la época del entrenamiento. Aun así tiene una importancia de 0.10 en RF y 0.08 en XGB, y probablemente contribuye a que R² sea negativo. | Quitarla. Si importa la hora, usar variables cíclicas como hora del día o segundos desde el inicio del ciclo. |
| A2 | recolector.py:25-26 | `except Exception: return 0.0`: un timeout o un error se guarda como latencia de 0 ms. | Justo los picos que se quieren predecir (respuestas que tardan más de 2 s o fallan) se registran como la mejor latencia posible. Eso contamina el objetivo. Además oculta errores de conexión, por ejemplo si el servidor se cae. | Guardar `NaN` o una columna `Estado` (ok, timeout, error). Capturar `requests.RequestException` y no `Exception`. Registrar el tipo de error. |
| A3 | recolector.py:9 y :33 | La ruta es relativa al directorio de trabajo (`'../data/raw/...'`) y el archivo se abre en modo `'w'` cada vez que arranca. | Si se ejecuta desde otra carpeta, escribe en un lugar inesperado. Si se vuelve a ejecutar, **sobrescribe sin aviso** el dataset anterior, que son horas de recolección. | Construir la ruta con `Path(__file__).resolve().parent.parent / "data/raw"`. Generar un nombre con fecha y hora, o abortar si el archivo ya existe. Recibirla como argumento CLI (`argparse`). |
| A4 | requirements.txt | Falta `requests`, que importa recolector.py:4. Tampoco está instalado en `venv/`. | El recolector no se puede reproducir desde `requirements.txt`. Falla con `ModuleNotFoundError`. | Agregar `requests==<versión>`. |

## Medio

| # | Archivo / línea | Hallazgo | Riesgo | Corrección |
|---|---|---|---|---|
| M1 | analisis.ipynb, celda 25 | Las conclusiones no coinciden con las salidas. Dicen "recall 0.29", pero la celda 18 muestra 0.27. Dicen "máximo ~6.5 ms", pero en `registro_rendimiento2.csv` la latencia máxima es **35.28 ms** y 41 casos de test superan 6.54 ms. | Las conclusiones del informe son incorrectas. | Generar las cifras desde variables o revisarlas tras cada ejecución. |
| M2 | analisis.ipynb, celdas 20 y 24 (`execution_count=None`) y celda 22 (exec 11 después de 9) | El notebook no se ejecutó de forma lineal. Algunas salidas vienen de ejecuciones anteriores. | Los resultados no son reproducibles y puede haber estado oculto. | "Restart & Run All" antes de commitear. |
| M3 | analisis.ipynb, celdas 12 a 22 | No hay un modelo base de persistencia (predecir que la latencia futura es igual a la actual). Tampoco se usa la latencia actual ni retardos (lags) como variables. La validación es un único split 80/20. | Con R² < 0 no se sabe si el problema es el modelo o los datos. Las métricas de un solo split son inestables. | Agregar `Latencia_ms` y sus lags y medias móviles como variables. Comparar contra la persistencia. Usar `TimeSeriesSplit`. |
| M4 | analisis.ipynb, celdas 8 y 22 | El horizonte se calcula con `shift(-6)`, que supone un muestreo exacto cada 5 s. | `registro_rendimiento.csv` tiene **756 huecos de más de 6 s** (el mayor de 94 s). Ahí el desplazamiento no equivale a 30 s. Con el dataset 2 no hay problema porque no tiene huecos. | Unir por tiempo con `merge_asof` o `reindex` a una frecuencia fija y validar los huecos antes. |
| M5 | estresador.sh:32-35 | `--vm 2 --vm-bytes 1G` reserva unos 2 GB (1 GB por worker), aunque el mensaje dice "1GB". Según los CSV, el servidor tiene unos 1.6 GB de RAM en total. | Puede usar swap o activar el OOM killer, que podría matar el servidor web que se está midiendo y producir datos espurios. | Usar `--vm 1 --vm-bytes 60%`, o corregir el valor y el mensaje. |
| M6 | estresador.sh:35-37 | No se comprueba que `stress-ng` exista ni su código de salida. Siempre imprime "completada con éxito". | Si stress-ng no está instalado, el experimento "termina" sin generar estrés y no se nota. | Al inicio, `command -v stress-ng \|\| exit 1`. Después, `if ! stress-ng ...; then echo "falló" >&2; fi`. |
| M7 | analisis.ipynb, celda 2 | `pip install` sin versiones fijadas dentro del notebook. | Puede instalar versiones distintas a `requirements.txt` (problema de reproducibilidad y de cadena de suministro). | Eliminar la celda e instalar con `pip install -r requirements.txt`. |
| M8 | Todo el proyecto | No hay ningún test. | Las partes críticas sin cubrir son `obtener_latencia` (éxito, timeout y error), el formato del CSV, la creación del objetivo con `shift` y el split temporal. | Mover la lógica a funciones en `src/` y probarlas con `pytest`, usando un mock de `requests`, `psutil` y DataFrames sintéticos. |

## Bajo

| # | Archivo / línea | Hallazgo | Corrección |
|---|---|---|---|
| B1 | src/entrenamiento.py, README.md | Están vacíos: código muerto y falta de documentación. | Poner el pipeline de entrenamiento en `entrenamiento.py` y documentar en el README cómo ejecutar el experimento. |
| B2 | Arquitectura | Toda la lógica de ML está en el notebook. Lo mismo para limpieza, features y modelado; no hay `data/processed`. | Separar en módulos `src/features.py` y `src/modelos.py` e importarlos desde el notebook. |
| B3 | analisis.ipynb, celda 22 vs celdas 8 y 12 | `evaluate_horizon` duplica la ingeniería de características y el split. | Reutilizar una sola función `preparar_datos(df, shift)`. |
| B4 | estresador.sh:13-16 | El comentario dice "7 ciclos ≈ 140 min", pero `TOTAL_CICLOS=23` (unas 7.7 h ≈ 5520 muestras). El recolector se detiene en 5000 (recolector.py:11), antes de que termine el estrés. | Actualizar el comentario y alinear ambos valores, o pasarlos como parámetros. |
| B5 | recolector.py:59 | Usa `sleep(5)` fijo además del tiempo de la petición, que puede llegar a 2 s. El intervalo real se desfasa. | Programar con `time.monotonic()` y dormir solo lo que falte hasta el siguiente tick. |
| B6 | recolector.py:52-54 | Abre y cierra el archivo en cada muestra. A 0.2 Hz el impacto es despreciable y da durabilidad. | Opcional: mantenerlo abierto y llamar a `flush()` en cada escritura. |
| B7 | requirements.txt | Está codificado en UTF-16 LE (salida de `pip freeze >` en PowerShell). pip lo tolera, pero rompe a otras herramientas (Dependabot, pip-audit, grep). Mezcla dependencias de desarrollo (`debugpy`, `ipykernel`) con las de ejecución. | Volver a guardarlo en UTF-8. Separar en `requirements.txt` y `requirements-dev.txt`. |
| B8 | Dependencias | Hay paquetes desactualizados, todos menores salvo `pillow` 12→13 y `python-dateutil` 2.9→4.0. **No se verificaron CVEs** porque `pip-audit` no está instalado. | Ejecutar `pip install pip-audit && pip-audit -r requirements.txt` y actualizar con cuidado los saltos mayores. |
| B9 | analisis.ipynb, celda 20 | `RandomForestClassifier` sin `n_jobs=-1`, a diferencia del resto. | Unificar los parámetros. |
| B10 | Repositorio | El notebook se commitea con salidas e imágenes (el diff en ese momento era de unas 950 líneas). `registro_rendimiento2.csv` no está versionado, aunque es el dataset que usa el notebook. | Usar `nbstripout`. Decidir una política para los datos: versionarlos todos o usar Git LFS o DVC. |

## Rendimiento

Con unas 15 000 filas no hay problemas reales. No hay consultas a base de datos ni fugas de memoria. Los únicos puntos son B5 y B6, que son menores.

## Orden sugerido de corrección

1. **A1 y A2.** Invalidan los resultados actuales; después conviene volver a recolectar o reetiquetar los datos.
2. **A3, A4 y M5.** Protegen los datos y la reproducibilidad del experimento.
3. **M3 y M4.** Son las mejoras que más pueden cambiar las métricas del modelo.
4. **M8 y B2.** Tests y separar la lógica en módulos.
