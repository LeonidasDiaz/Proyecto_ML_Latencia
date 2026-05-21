#!/bin/bash

# ==========================================
# SCRIPT DE AUTOMATIZACIÓN DE PRUEBAS DE ESTRÉS
# PROYECTO ML - PREDICCIÓN DE LATENCIA
# ==========================================

echo "====================================================="
echo " Arrancando Ciclos de Estrés Automatizados"
echo " Presiona Ctrl+C para detener todo el experimento"
echo "====================================================="

# Definir la cantidad de ciclos (Cada ciclo dura 20 minutos en total)
# 7 ciclos x 20 minutos = ~140 minutos (Tiempo suficiente para superar 1,600 pings)
# Puedes ajustar este número según cuántas horas dejes el recolector encendido.
TOTAL_CICLOS=10

for ((i=1; i<=TOTAL_CICLOS; i++))
do
    echo ""
    echo "-----------------------------------------------------"
    echo " INICIANDO CICLO DE PRUEBA EXPERIMENTAL [$i/$TOTAL_CICLOS]"
    echo " Hora de inicio: $(date '+%H:%M:%S')"
    echo "-----------------------------------------------------"

    # FASE 1: USO NORMAL (Línea Base) - 10 Minutos
    echo "[FASE 1] Estado estable / Uso normal por 10 minutos (600 segundos)..."
    sleep 600

    # FASE 2: PICO DE SATURACIÓN (Estrés Súbito) - 5 Minutos
    echo "[FASE 2] ¡Lanzando pico de estrés por 5 minutos!"
    echo "Saturando 4 cores de CPU y alojando 1GB de RAM de forma artificial..."
    
    # Ejecutamos stress-ng durante 300 segundos (5 minutos)
    stress-ng --cpu 4 --vm 2 --vm-bytes 1G --timeout 300s

    echo "Fase de estrés completada con éxito."

    # FASE 3: RECUPERACIÓN (Descanso de Hardware) - 5 Minutos
    echo "[FASE 3] Servidor en fase de recuperación por 5 minutos (300 segundos)..."
    sleep 300

    echo "Ciclo [$i] finalizado correctamente."
done

echo "====================================================="
echo "¡Fase experimental completada! Todos los ciclos de estrés terminaron."
echo "====================================================="