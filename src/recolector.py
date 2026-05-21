import psutil
import time
import csv
from ping3 import ping
from datetime import datetime
import os

# Configuración
ARCHIVO_CSV = '../data/raw/registro_rendimiento.csv'
INTERVALO_SEGUNDOS = 5
MAX_REGISTROS = 10000

# Asegurar que el directorio exista
os.makedirs(os.path.dirname(ARCHIVO_CSV), exist_ok=True)

def obtener_latencia():
    """
    Mide la latencia del servidor. 
    Hacemos ping a localhost (127.0.0.1) o al router local para medir la respuesta de la red interna.
    Devuelve la latencia en milisegundos.
    """
    try:
        # ping3 devuelve el tiempo en segundos, lo multiplicamos por 1000 para ms
        tiempo_respuesta = ping('127.0.0.1', timeout=2) 
        if tiempo_respuesta is not None:
            return round(tiempo_respuesta * 1000, 2)
        return 0.0
    except Exception as e:
        return 0.0

def iniciar_monitoreo():
    print(f"Iniciando recolección de datos. Guardando en: {ARCHIVO_CSV}")
    print("Presiona Ctrl+C para detener manualmente.\n")
    
    # Escribir la cabecera del CSV
    with open(ARCHIVO_CSV, mode='w', newline='') as archivo:
        writer = csv.writer(archivo)
        # Columnas exactas que declaraste en tu proyecto
        writer.writerow(['Timestamp', 'CPU_Percent', 'RAM_Utilizada_MB', 'RAM_Libre_MB', 'RAM_Percent', 'Latencia_ms'])

    registros_actuales = 0

    try:
        while registros_actuales < MAX_REGISTROS:
            # 1. Timestamp (Hora exacta)
            timestamp_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 2. Consumo de CPU (%)
            cpu_percent = psutil.cpu_percent(interval=None) # Lectura instantánea
            
            # 3. Consumo de RAM
            memoria = psutil.virtual_memory()
            ram_percent = memoria.percent
            ram_usada_mb = round(memoria.used / (1024 * 1024), 2)
            ram_libre_mb = round(memoria.available / (1024 * 1024), 2)
            
            # 4. Latencia de respuesta
            latencia_ms = obtener_latencia()
            
            # Guardar en CSV
            with open(ARCHIVO_CSV, mode='a', newline='') as archivo:
                writer = csv.writer(archivo)
                writer.writerow([timestamp_actual, cpu_percent, ram_usada_mb, ram_libre_mb, ram_percent, latencia_ms])
            
            registros_actuales += 1
            print(f"[{registros_actuales}/{MAX_REGISTROS}] {timestamp_actual} | CPU: {cpu_percent}% | RAM: {ram_percent}% | Latencia: {latencia_ms}ms")
            
            # Esperar 5 segundos antes de la siguiente lectura
            time.sleep(INTERVALO_SEGUNDOS)
            
    except KeyboardInterrupt:
        print("\nRecolección interrumpida por el usuario.")
    
    print("\n¡Proceso finalizado! Los datos están listos para tu modelo predictivo.")

if __name__ == "__main__":
    # Inicializar la lectura de CPU para mayor precisión
    psutil.cpu_percent(interval=1)
    iniciar_monitoreo()