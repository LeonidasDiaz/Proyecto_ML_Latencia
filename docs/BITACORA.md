# Bitácora del proyecto: Predicción de latencia con ML

Bitácora reconstruida el 2026-11-01 a partir de los archivos del repositorio. No había documentación previa (el `README.md` está vacío). El autor recuerda solo que fue un **proyecto de investigación**.

**Fuentes usadas:** código de `src/`, historial de git (`git log`, `git show`), versión commiteada y versión actual de `notebooks/analisis.ipynb`, contenido de los CSV de `data/raw/` y fechas de modificación de los archivos.

**Regla de esta bitácora:** solo se registra lo que se puede verificar en los archivos. Lo que no se puede verificar queda como **pregunta abierta**. Cuando un valor no tiene explicación en ningún archivo, se escribe **"valor elegido sin justificación documentada"**.

Niveles de confianza:
- **Alta:** el hecho está escrito literalmente en el código o en git, o varias fuentes independientes coinciden.
- **Media:** es una inferencia coherente con varias evidencias, pero indirecta.
- **Baja:** la evidencia es compatible, pero hay otras explicaciones posibles.

---

## 1. Línea de tiempo reconstruida

Las horas del commit y de los archivos están en hora local de Windows (UTC−6). Las de los CSV están en el reloj del servidor, que según la sección 2.1 es UTC; entre paréntesis va su equivalente local.

| Fecha y hora local (UTC−6) | Evento | Evidencia |
|---|---|---|
| 2026-05-20 18:00 | Commit inicial. `recolector.py` mide la latencia con **ping ICMP** (`ping3`) a `127.0.0.1`, con `MAX_REGISTROS = 10000`. `.gitignore` excluye `.ubuntu-26.04-live-server-amd64.iso`. | `git show bd720dc` |
| 2026-05-20 19:50 | Se agrega `estresador.sh` con `TOTAL_CICLOS=10`. | `git show ac8793b` |
| 2026-05-20 22:34 | Empieza la recolección del **dataset 1**. | 1.ª fila del CSV: `2026-05-21 04:34:49` UTC |
| 2026-05-21 01:13 | `TOTAL_CICLOS` cambia de 10 a **34**. | `git show b05df51` |
| ≈ 2026-05-21 02:03 | El estresador se vuelve a lanzar, tras 10 ciclos. | Ver sección 2.4 |
| 2026-05-21 15:25 | Termina el dataset 1 (10 000 filas). | Última fila: `21:25:40` UTC |
| 2026-05-21 15:46 | El CSV del dataset 1 llega a Windows. | Fecha de modificación del archivo |
| 2026-05-22 13:52 | Se crea `venv/` en Windows y se genera `requirements.txt` (UTF-16, típico de `pip freeze >` en PowerShell). | Fechas de modificación |
| 2026-05-22 18:08–18:15 | `recolector.py` cambia de ping ICMP a **HTTP GET a `127.0.0.1:8080`** con `MAX_REGISTROS = 5000`. `TOTAL_CICLOS` pasa de 34 a **23**. Se commitean el notebook (que analiza el dataset 1) y el dataset 1. Mensaje del commit: "arreglando errores". | `git show ab40aa8` |
| 2026-05-22 18:32 | Empieza el **dataset 2**, 17 min después del commit anterior. | 1.ª fila: `2026-05-23 00:32:29` UTC |
| 2026-05-23 01:29 | Termina el dataset 2 (5000 filas). | Última fila: `07:29:32` UTC |
| 2026-05-23 06:56 | El dataset 2 llega a Windows como `registro_rendimiento2.csv`. Nunca se commiteó. | Fecha de modificación; `git status` |
| Después del 2026-05-22 | El notebook se reescribe (sin commitear) para analizar el dataset 2: pasa de 10 a 26 celdas y agrega conclusiones. | `git diff` del notebook |
| 2026-11-01 | El notebook se reproduce desde cero y todas las métricas coinciden con el documento final, salvo una diferencia de redondeo en el R² de RF a 5 s (sección 2.10). Se corrigen las conclusiones y se versiona por fin el dataset 2. | Commit de esa fecha |

---

## 2. Hallazgos deducidos de los archivos

### 2.1 El servidor era Ubuntu Server 26.04, probablemente en una máquina virtual

- **Ubuntu Server 26.04.** El `.gitignore` del commit inicial excluía `.ubuntu-26.04-live-server-amd64.iso`. Eso indica que el instalador estaba en la carpeta del proyecto. La línea se borró en el commit `ab40aa8`. **Confianza: media.** Que el ISO estuviera ahí no prueba que se haya instalado.
- **Máquina virtual.** `estresador.sh` usa `stress-ng` y Bash, así que el sistema era Linux. Pero `venv/` y el notebook están en Windows. El recolector y el estresador tenían que estar en la misma máquina, porque los picos de CPU al 100 % aparecen en los datos. **Confianza: media.**
- **RAM total de unos 1.64 GB.** La RAM total se calcula como `RAM_Libre_MB / (1 − RAM_Percent/100)` y da lo mismo en ambos datasets, así que ambos vienen de la misma máquina. **Confianza: alta.**
- **El reloj del servidor estaba en UTC.** Los CSV terminan *después* de la hora local en que fueron copiados a Windows (por ejemplo, el dataset 2 termina a las 07:29 y fue copiado a las 06:56 locales). Con un desfase de +6 h todo cuadra: el inicio del dataset 2 cae 17 min después del commit que introdujo HTTP. UTC es el valor por defecto de Ubuntu Server. **Confianza: alta** en que el reloj no estaba en hora local. **Confianza: media-alta** en que era UTC exacto.
  - Consecuencia: la columna `Timestamp` está en UTC, no en hora local.

### 2.2 Por qué el dataset 1 tiene 10 000 filas

En el momento en que se recolectó, `MAX_REGISTROS` valía `10000`. Se cambió a `5000` en el commit `ab40aa8`, después de la recolección. **Confianza: alta.**

### 2.3 Por qué la latencia cambió de ~0.1 ms a ~2 ms

Los dos datasets **no miden lo mismo**:

| | Dataset 1 | Dataset 2 |
|---|---|---|
| Método | Ping ICMP a `127.0.0.1` (`ping3`) | `GET http://127.0.0.1:8080/` (`requests`) |
| Latencia | 0.09 – 0.79 ms | 1.08 – 35.28 ms |
| Qué mide realmente | Ida y vuelta por la interfaz de loopback del kernel | Tiempo de respuesta de una aplicación web |

**Confianza: alta.** El dataset 1 se recolectó entre el commit inicial y el `ab40aa8`, y en ese periodo el código usaba `ping3`.

Una observación relacionada: la RAM usada en reposo sube de unos 210 MB (dataset 1) a unos 370 MB (dataset 2). Eso es compatible con que en el dataset 2 hubiera un servidor web corriendo, pero hay otras explicaciones posibles. **Confianza: baja.**

### 2.4 Cuántos ciclos de estrés se ejecutaron realmente

Los episodios de estrés se detectaron como rachas de 10 o más muestras seguidas con CPU ≥ 90 %.

- **Dataset 1:** 49 episodios, uno cada ~20.4 min, de ~4.8 min cada uno. Entre el episodio 10 y el 11 hay un intervalo de 25.1 min en lugar de 20, lo que indica que **el estresador se relanzó tras 10 ciclos**. Coincide con `TOTAL_CICLOS=10` de ese momento. Después hubo **al menos 39 ciclos más**, aunque el valor commiteado era 34 (ver pregunta abierta P5). **Confianza: alta** en el relanzamiento; la discrepancia 39 vs 34 no tiene explicación.
- **Dataset 2:** 21 episodios, uno cada 20.0 min. El estresador estaba configurado a 23 ciclos (~7.7 h), pero el recolector se detuvo a las 5000 muestras (~6.95 h), antes de que se completaran los ciclos 22 y 23. **Confianza: alta.**

### 2.5 Qué significa el comentario de "1,600 pings"

El comentario de `estresador.sh` dice "7 ciclos × 20 minutos = ~140 minutos (Tiempo suficiente para superar 1,600 pings)". La cuenta es 140 min × 60 / 5 s = 1680 muestras > 1600. O sea, en algún momento el objetivo fue recolectar al menos 1600 muestras, y la palabra "pings" viene de la época del ping ICMP. El comentario nunca se actualizó: el script se commiteó con 10 ciclos, no 7. **Confianza: alta** en la cuenta. El origen de la cifra 1600 está en la pregunta abierta P4.

### 2.6 Evolución del análisis

- **Versión commiteada del notebook** (10 celdas, dataset 1): R² de −0.09 (Random Forest) y −0.14 (XGBoost). Umbral de pico de 0.1821 ms. Recall de picos de 0.00: no detectó ninguno de los 63 picos.
- **Versión actual sin commitear** (26 celdas, dataset 2): R² de −0.23 y −0.71. Umbral de 6.54 ms. Recall de picos de 0.27 con XGBoost y de 0.00 con Random Forest balanceado.
- El cambio de dataset es un hecho. El motivo no está documentado (pregunta abierta P7).

### 2.7 Contradicciones entre las conclusiones y los datos

Las conclusiones de la versión reescrita del notebook (la celda de conclusiones) no coincidían con los datos:

- Decían "recall 0.29", pero la salida muestra **0.27**. **Corregido el 2026-11-01.**
- Decían "latencia máxima ~6.5 ms", pero la máxima del dataset 2 es **35.28 ms**. 6.54 ms es el umbral de pico, no el máximo. **Corregido el 2026-11-01:** ahora dice "umbral de pico 6.54 ms; máximo observado 35.28 ms".
- Dicen que la latencia "apenas se degradó bajo estrés". Esta frase se mantiene porque es la conclusión del documento final, pero los datos la matizan (sección 2.10).

### 2.8 Pistas sobre cómo se escribió el código

Varios comentarios hablan en segunda persona al autor:
- "Columnas exactas que **declaraste en tu proyecto**" (`recolector.py`, commit inicial).
- "Como **tomaste** datos cada 5 segundos…" y "**tu** CSV ya lo está" (notebook commiteado).

Esto sugiere que parte del código se escribió con ayuda externa, de un asistente o un tutor. También sugiere que existía un documento previo del proyecto (una propuesta o protocolo) que definía las columnas. Ese documento no está en el repositorio. **Confianza: media.**

### 2.9 Huecos en el muestreo del dataset 1

- El dataset 1 tiene 756 intervalos de más de 6 s, de entre 6 y 94 s. El intervalo medio es 6.07 s, frente a 5.01 s del dataset 2, que no tiene huecos.
- Los huecos **no** ocurren durante el estrés. En todas esas filas la CPU es menor al 90 % y la mayoría están en los 15 min posteriores a un episodio de estrés.
- No hay ningún valor `0.0` de latencia, así que no fueron pings fallidos registrados como error.
- La causa no se puede deducir (pregunta abierta P6).

### 2.10 Reproducción del notebook (2026-11-01)

**Reproducción desde cero.** El notebook se ejecutó de principio a fin con un kernel nuevo (equivalente a "Restart & Run All"), sin cambiar la lógica. Solo se eliminó la celda de `pip install`. Las 11 celdas de código se ejecutaron en orden y sin errores. **Todas las métricas coinciden con el documento final, salvo el R² de Random Forest a 5 s:** da −0.3281, que redondea a −0.33, y el documento lo reporta como −0.32. Es una diferencia de redondeo.

| Métrica | Documento | Reproducción |
|---|---|---|
| R² Random Forest | −0.23 | −0.2327 |
| R² XGBoost | −0.71 | −0.7050 |
| Recall de picos (XGBoost sin balanceo) | 0.27 | 0.27 |
| Recall de picos (RF balanceado) | 0.00 | 0.00 |
| Umbral de pico | 6.54 ms | 6.5382 ms |
| Matriz de confusión (XGBoost) | `[[876, 82], [30, 11]]` | `[[876, 82], [30, 11]]` |
| RMSE a 5, 10 y 30 s (RF) | 1.88 / 1.90 / 1.82 ms | 1.8837 / 1.9008 / 1.8157 ms |
| R² a 5, 10 y 30 s (RF) | −0.32 / −0.35 / −0.23 | **−0.3281** / −0.3523 / −0.2327 |

**Confianza: alta.**

**La latencia sí se degradó bajo estrés.** En el dataset 2, la mediana de latencia es de **4.26 ms** en las muestras con CPU ≥ 90 % y de **1.69 ms** en el resto, unas **2.5 veces más**. El máximo observado es 35.28 ms. Esto matiza la conclusión del documento y del notebook de que la latencia "apenas se degradó": el aumento relativo es claro, aunque en valores absolutos siga siendo de pocos milisegundos. **Confianza: alta** en las cifras. Si el aumento es "poco" o "mucho" es una cuestión de interpretación que no corresponde a esta bitácora.

---

## 3. Valores elegidos sin justificación documentada

| Valor | Dónde | Lo único que documentan los archivos |
|---|---|---|
| Horizonte de predicción de 30 s | Notebook, `shift(-6)` | Que 30 s equivalen a 6 filas a 5 s por fila. No explica por qué 30 s. |
| Umbral de pico = media + 2σ del entrenamiento | Notebook, celda 18 | Nada. |
| Intervalo de muestreo de 5 s | `recolector.py:10` | Nada. |
| Fases del ciclo: 10 min base, 5 min estrés, 5 min recuperación | `estresador.sh:28,35,41` | Solo los nombres de las fases ("Línea Base", "Estrés Súbito", "Recuperación"). |
| `TOTAL_CICLOS` = 10 → 34 → 23 | `estresador.sh:16` | El historial de git. 23 ciclos (~7.7 h) alcanzan para cubrir 5000 muestras (~6.95 h), pero eso no está escrito en ningún lado. |
| `MAX_REGISTROS` = 10000 → 5000 | `recolector.py:11` | El historial de git. |
| Objetivo de "1,600 pings" | Comentario de `estresador.sh:14` | Nada sobre el origen de la cifra. |
| `stress-ng --cpu 4 --vm 2 --vm-bytes 1G` | `estresador.sh:35` | El mensaje dice "1GB de RAM". Con 2 workers de 1 GB se reservan unos 2 GB en una máquina de ~1.64 GB. |
| Timeout HTTP de 2 s; 0.0 como valor de error | `recolector.py:21,26` | Nada. |
| Split 80/20 temporal | Notebook, celda 12 | Solo que el split respeta el orden cronológico. |
| `n_estimators=100`, `learning_rate=0.1`, `random_state=42` | Notebook, celda 14 | Nada. Son los valores típicos por defecto. |
| Horizontes comparados de 5, 10 y 30 s | Notebook, celda 22 | Nada. |

---

## 4. Preguntas abiertas

Estas preguntas no se pueden responder con los archivos del repositorio.

- **P1. Aplicación en el puerto 8080.** ¿Qué aplicación respondía en `127.0.0.1:8080` durante el dataset 2 y qué devolvía la ruta `/`? No aparece en el repositorio.
- **P2. Plataforma de virtualización.** ¿El servidor Ubuntu corría en una VM? Si es así, ¿con qué hipervisor (VirtualBox, VMware, Hyper-V, otro) y con cuántos núcleos de CPU? El número de núcleos importa para interpretar `--cpu 4`.
- **P3. Horizonte de 30 s.** ¿Por qué se eligió predecir a 30 s? Valor elegido sin justificación documentada.
- **P4. Diseño del experimento.** ¿De dónde salen las duraciones 10/5/5 min, la cifra de 1600 muestras y los parámetros de `stress-ng`? Valores elegidos sin justificación documentada.
- **P5. Segunda corrida del dataset 1.** El valor commiteado era `TOTAL_CICLOS=34`, pero los datos muestran al menos 39 ciclos en esa corrida. ¿El script del servidor tenía otro valor, o se relanzó más de una vez?
- **P6. Huecos del dataset 1.** ¿Qué causó los 756 huecos de muestreo (de hasta 94 s) fuera de las fases de estrés?
- **P7. Cambio de ping ICMP a HTTP.** ¿Por qué se cambió? ¿Se descartó el dataset 1 porque el ping a loopback no mide la latencia de un servidor? El commit solo dice "arreglando errores".
- **P8. Renombrado del dataset 2.** ¿Se renombró a `registro_rendimiento2.csv` al copiarlo para no sobrescribir el dataset 1? ¿Por qué no se commiteó?
- **P9. Umbral de pico.** ¿Por qué media + 2σ? Valor elegido sin justificación documentada.
- **P10. `src/entrenamiento.py`.** Está vacío desde el commit inicial y nunca se modificó. ¿Cuál era su propósito?
- **P11. Documento original del proyecto.** ¿Existe la propuesta o protocolo de investigación al que alude el comentario "declaraste en tu proyecto"? ¿Dónde está? Podría responder P3, P4 y P9.
- **P12. Destino de la investigación.** ¿Para qué institución, curso o publicación era? ¿Hubo un informe final? Si lo hubo, ¿qué conclusiones reportó, dado que las del notebook contradicen los datos (sección 2.7)?
