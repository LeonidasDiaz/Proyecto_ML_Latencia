# Contexto de la investigación

> **Fuente:** documento final de la investigación *"Predicción de latencia en servidores mediante algoritmos de Machine Learning basados en el consumo de recursos"*, Leonidas Díaz Flores, Universidad Mundo Maya, junio de 2026.
>
> Este archivo resume ese documento para dar contexto al código. Cada punto se marca como:
> - **Confirmado**: lo dice el documento.
> - **Deducido**: se infiere al cruzar el documento con el código o los datos. Hay que verificarlo.
> - **Sin justificación documentada**: no aparece en ningún lado.

---

## 1. Resumen de la investigación

| | |
|---|---|
| **Pregunta** | ¿De qué manera un modelo de Machine Learning supervisado permite predecir los picos de latencia de un servidor a partir del historial de consumo de CPU y RAM? |
| **Hipótesis** | Un modelo supervisado permite predecir los picos de latencia a partir del historial de CPU y RAM. |
| **Objetivo general** | Evaluar si Random Forest y XGBoost, entrenados con datos históricos de CPU y RAM, pueden predecir la latencia futura con **30 s de antelación** en un entorno controlado. |
| **Diseño** | Cuantitativo, experimental, con alcance explicativo. El propio servidor funciona como su control (fases de reposo, estrés y recuperación). |
| **Resultado** | **La hipótesis se refutó** bajo las condiciones del experimento. R² negativo en ambos modelos, recall de picos de 0.27, y recall de 0.00 al balancear las clases. |
| **Conclusión principal** | Tener métricas instantáneas de CPU y RAM no basta. Hace falta una señal de degradación más fuerte y variables dinámicas (lags, medias móviles, fase del ciclo). |

## 2. Entorno experimental (Confirmado)

- **Máquina:** VM con Ubuntu Server de 64 bits, dedicada al experimento. Especificaciones "aproximadas": 2 vCPU, 4 GB de RAM y 20 GB de SSD.
- **Servidor medido:** `python3 -m http.server 8080 &`, comprobado con `curl`.
- **Por qué HTTP y no ping:** se descartó ICMP (ping a 127.0.0.1) porque el loopback lo gestiona el kernel y no refleja la saturación de CPU en espacio de usuario.
- **Recolección:** dos terminales SSH en paralelo.
  - Terminal 1: `python3 recolector.py` (una muestra cada 5 s hasta llegar a 5 000 registros).
  - Terminal 2: `bash estresador.sh` (**21 ciclos** de 20 min: 10 min normal, 5 min de estrés con `stress-ng --cpu 4 --vm 2 --vm-bytes 1G` y 5 min de recuperación).
  - Duración: unas 7 horas. Salida: `registro_rendimiento.csv`.
- **Transferencia:** `scp` al equipo local y análisis en Jupyter. Versionado con Git y GitHub.
- **Dependencias en la VM:** `python3-requests` y `python3-psutil`.

## 3. Análisis (Confirmado)

- **Variables independientes:** `CPU_Percent`, `RAM_Utilizada_MB`, `RAM_Libre_MB`, `RAM_Percent` y `Timestamp_Num` (timestamp convertido a número).
- **Variable dependiente:** latencia a 30 s (desplazamiento temporal). Quedan 4 994 filas válidas después de quitar las 6 filas con NaN que genera el desplazamiento.
- **Modelos:** Random Forest (100 estimadores) y XGBoost (100 estimadores, `learning_rate=0.1`).
- **División:** temporal, 80 % de los datos más antiguos para entrenamiento y 20 % para prueba (999 registros, del 2026-05-23 06:05:46 al 07:29:02).
- **Pico:** latencia futura > media + 2σ del conjunto de entrenamiento = **6.54 ms**.
- **Experimentos complementarios:** importancia de variables, horizontes de 5, 10 y 30 s, y balanceo con `class_weight="balanced"` en Random Forest.

## 4. Resultados reportados en el documento

**Regresión (horizonte de 30 s).** La desviación estándar de la latencia futura en el conjunto de prueba es de 1.64 ms.

| Modelo | RMSE (ms) | MAE (ms) | R² |
|---|---|---|---|
| Random Forest | 1.82 | 1.21 | −0.23 |
| XGBoost | 2.14 | 1.31 | −0.71 |

**Horizonte (Random Forest).**

| Horizonte | RMSE (ms) | R² |
|---|---|---|
| 5 s | 1.88 | −0.32 |
| 10 s | 1.90 | −0.35 |
| 30 s | 1.82 | −0.23 |

**Clasificación de picos (umbral de 6.54 ms; 41 picos reales en 999 muestras de prueba).**

| Modelo | Precisión | Recall | F1 | Accuracy |
|---|---|---|---|---|
| XGBoost sin balanceo | 0.12 | 0.27 | 0.16 | 0.89 |
| Random Forest balanceado | 0.00 | 0.00 | 0.00 | 0.95 |

Matriz de confusión de XGBoost: `[[876, 82], [30, 11]]`.

**Importancia de variables:** `CPU_Percent` es la más importante (38.2 % en RF y 63.3 % en XGB). `Timestamp_Num` tiene entre 8 % y 10 %. Todas las correlaciones con la latencia futura son débiles (|r| < 0.3).

## 5. Respuestas a las preguntas abiertas

| # | Pregunta | Respuesta | Estado |
|---|---|---|---|
| 1 | ¿Qué servidor respondía en `127.0.0.1:8080`? | `python3 -m http.server 8080` en una VM con Ubuntu Server. | Confirmado |
| 2 | ¿Por qué un horizonte de 30 s? | Los 30 s aparecen en el objetivo general, pero no se explica por qué ese valor. La matriz de congruencia (p. 36) solo justifica anticipar en general: "dándole tiempo al administrador de solucionarlo antes de que afecte a los usuarios". | Valor elegido sin justificación documentada |
| 3 | ¿Por qué el umbral media + 2σ? | El documento lo llama "umbral estadístico", sin citar fuente. | Sin justificación documentada |
| 4 | ¿Por qué ciclos de 10/5/5 min y cuántos? | Las tres fases (basal, estrés y recuperación) buscan "garantizar la variabilidad de los datos". El documento dice **21 ciclos**, el código tiene `TOTAL_CICLOS=23` y el comentario dice 7. Las duraciones no se justifican. | Parcial: las duraciones no tienen justificación documentada; 21 vs 23 está explicado en la sección 6 |
| 5 | ¿Por qué el dataset 1 tiene 10 000 filas y huecos? | El documento no lo menciona. | Sin justificación documentada |
| 6 | ¿Por qué la latencia pasó de ~0.1 ms a ~2 ms entre datasets? | El dataset 1 se midió con **ping ICMP** al loopback, y el dataset 2 con HTTP. El documento dice que se descartó ICMP porque el kernel gestiona el loopback y no refleja la saturación de CPU (p. 20). El commit `bd720dc` lo confirma: esa versión de `recolector.py` usaba `ping3` y `MAX_REGISTROS = 10000`. El documento reporta una latencia basal HTTP de ~1.5 ms, que encaja con el dataset 2. | Confirmado (p. 20 y `git show bd720dc:src/recolector.py`) |
| 7 | ¿El dataset 1 se descartó a propósito? | Si lo anterior es correcto, sí: era la versión con ping. El documento llama `registro_rendimiento.csv` al dataset final, pero el notebook usa `registro_rendimiento2.csv`, así que probablemente se renombró. | **Deducido** |
| 8 | ¿Para qué es `entrenamiento.py`? | No se menciona. Todo el análisis se hizo en Jupyter. Lo más probable es que fuera una refactorización planeada y nunca hecha. | Sin justificación documentada |
| 9 | ¿Cuál es el contexto del proyecto? | Proyecto de investigación de la Universidad Mundo Maya, entregado en junio de 2026. | Confirmado |

## 6. Discrepancias entre el documento, el código y los datos

Hay que tenerlas en cuenta al escribir el README del portafolio, para no repetir errores.

| Tema | Documento | Código / datos | Qué hacer |
|---|---|---|---|
| **Latencia máxima** | Resumen y discusión: "picos máximos de 6.54 ms". | 6.54 ms es el **umbral** de pico, no el máximo. El propio documento cuenta 41 picos por encima de 6.54 ms. En el CSV, el máximo es **35.28 ms**. | En el README, escribir "umbral de pico 6.54 ms; máximo observado 35.28 ms". |
| **Signo de R²** | En "Prueba de hipótesis" aparece "Random Forest: 0.23; XGBoost: 0.71", sin el signo negativo. | La tabla dice −0.23 y −0.71. | Usar los valores negativos. |
| **Número de ciclos** | 21 ciclos. | `TOTAL_CICLOS=23`; el comentario dice 7. En el dataset 2 hay exactamente 21 episodios de estrés: el recolector se detuvo a las 5000 muestras (~6.95 h), antes de los ciclos 22 y 23 (23 ciclos ≈ 7.7 h). | **No es un error:** el documento reporta los ciclos que se ejecutaron mientras el recolector estaba activo (21) y el código, los configurados (23). Solo el comentario de "7 ciclos" está desactualizado (auditoría B4). La captura "[1/23]" de los anexos (p. 45) confirma que `TOTAL_CICLOS=23` era el valor configurado en la VM. Esa captura es de la corrida del 2026-05-28 (ver la fila "Captura del recolector"). Que también valiera 23 en la corrida del dataset 2 lo respalda git: el commit `ab40aa8` (2026-05-22) ya fijaba 23 y no hay commits posteriores. |
| **RAM de la VM** | 4 GB (aproximado). | **~1.64 GB, confirmado.** La captura del CSV en los anexos (p. 45) es la primera fila de `registro_rendimiento2.csv`: 411.25 MB usados, 1230.68 MB disponibles, 25.0 %. RAM total = disponible / (1 − 0.25) = 1640.9 MB. | Corregir a ~1.6 GB en el README. |
| **Memoria de stress-ng** | Cita el comando `stress-ng --cpu 4 --vm 2 --vm-bytes 1G` (p. 21). | Reserva unos 2 GB (1 GB por worker) en una VM de ~1.6 GB. El "1GB de RAM" solo aparece en el `echo` de `estresador.sh:32`, no en el documento. Riesgo de swap u OOM (auditoría M5). | Mencionarlo como limitación. |
| **Workers de CPU** | La VM tenía 2 vCPU (pp. 16–17). | `stress-ng --cpu 4` lanza 4 workers de CPU, el doble que núcleos disponibles. Satura la CPU, pero los workers compiten entre sí y con el servidor HTTP por solo 2 núcleos. | Mencionarlo como limitación del diseño de la carga. |
| **Exclusión de caídas** | "Se descartaron registros con caídas de red o errores de lectura". | `recolector.py` guarda los errores y timeouts como `0.0`, así que no se podían distinguir ni excluir (auditoría A2). | Verificar si hay valores `0.0` en el CSV y declararlo como limitación. `registro_rendimiento2.csv` no tiene ningún `0.0`. |
| **Captura del recolector** (anexos, p. 45) | Se presenta como imagen del proceso experimental. | Es de **otra corrida**, del 2026-05-28 desde las 02:23:34, con todas las latencias en `0.0 ms`. Probablemente `http.server` no estaba activo y el recolector guardó los errores como `0.0` (auditoría A2). No es el dataset analizado: `registro_rendimiento2.csv` empieza el 2026-05-23 00:32:29. No hay CSV ni commit de esa corrida en el repositorio. | Si se reutiliza la captura, aclarar que es de una corrida posterior y no del dataset analizado. |
| **Nombre del dataset** | `registro_rendimiento.csv`. | El notebook usa `registro_rendimiento2.csv`. | Aclararlo en `docs/DATOS.md`. |
| **Recall** | 0.27 (correcto). | Las conclusiones del notebook dicen 0.29 (auditoría M1). | Corregir el notebook a 0.27. |
| **`Timestamp_Num`** | Se usa como predictor; el documento reconoce que no captura la periodicidad. | La auditoría A1 explica que con un split temporal esta variable no puede generalizar. | Mencionarlo como causa adicional del bajo rendimiento. |

### Contradicciones internas del documento

| Tema | Una parte dice | Otra parte dice |
|---|---|---|
| **Tipo de estudio** | "Experimental puro con alcance explicativo" (resumen, p. 3; "Tipo de estudio", p. 17). | "Investigación correlacional", con cita de Hernández Sampieri (matriz de congruencia, p. 39). |
| **Transferencia de datos** | "El control de versiones y la transferencia de datos entre el servidor y el entorno de análisis se gestionó mediante Git y repositorios de GitHub" (p. 17). | "El dataset se transfirió al entorno de análisis local mediante scp" (p. 21). |

## 7. Trabajos futuros propuestos en el documento → posible versión 2

| Propuesta del documento | Relación con la auditoría |
|---|---|
| (a) Cambiar `http.server` por Nginx o Apache con contenido dinámico y tráfico concurrente. | Señal de degradación más fuerte. |
| (b) Variables derivadas (tasas de cambio, medias móviles, fase del ciclo) y métricas extra (I/O wait, conexiones activas). | Auditoría M3: lags, medias móviles y baseline de persistencia. |
| (c) Modelos de series temporales (LSTM, Transformers) y detección de anomalías no supervisada. | Después de M3 y M4. |
| (d) Repetir el experimento con Docker y patrones de carga irregulares. | Reproducibilidad (A3, A4, M5, M6). |

## 8. Erratas del PDF

Los números de página son los del visor de PDF, que van un número por delante de la numeración impresa en el cuerpo del documento.

| Página | Errata | Corrección |
|---|---|---|
| p. 3 | El nombre del autor aparece como "Leondias Diaz Floress". | Leonidas Díaz Flores. |
| p. 35 (Referencias) | Atribuye stress-ng a "Waterland, A. (2024)". Amos Waterland es autor del `stress` original. | stress-ng es obra de Colin Ian King. |
