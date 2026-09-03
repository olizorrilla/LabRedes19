import psutil
import time
import threading
from aux import *

UMBRAL_CPU = None
UMBRAL_MEM = None
IP_SERVIDOR = None
PUERTO_TCP = None

CLAVE = "clave_secreta"

lock_envio = threading.Lock()

def enviar_seguro(tcpSocket, mensaje):
    with lock_envio:
        enviar_mensaje(tcpSocket, mensaje)

def registrar_agente(tcpSocket, buffer):
    enviar_seguro(tcpSocket, f"REGISTER {CLAVE}")

    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)

    if respuesta == "REG_RESP":
        print("AGENTE REGISTRADO CORRECTAMENTE")
        return True, buffer
    
    print("NO SE PUDO REGISTRAR EL AGENTE")
    return False, buffer

def monitorear(tcpSocket):
    tiempo_transcurrido = 0

    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent

        tiempo_transcurrido += 1
        
        if cpu > UMBRAL_CPU:
            enviar_seguro(tcpSocket, f"ALERT CPU {cpu}")

        if mem > UMBRAL_MEM:
            enviar_seguro(tcpSocket, f"ALERT MEM {mem}")

        if tiempo_transcurrido >= 15:
            enviar_seguro(tcpSocket, f"METRIC CPU {cpu}")
            enviar_seguro(tcpSocket, f"METRIC MEM {mem}")
            tiempo_transcurrido = 0

def obtener_procesos():
    procesos = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']

            procesos.append(f"{pid}:{name}")

        except psutil.AccessDenied:
            continue

    return ", ".join(procesos)
            
def enviar_procesos(tcpSocket, buffer):
    while True:
        mensaje, buffer = recibir_mensaje(tcpSocket, buffer)

        if mensaje == "GET_PROC":
            procesos = obtener_procesos()
            enviar_seguro(tcpSocket, f"PROC {procesos}")
        elif mensaje == "ERROR":
            print("EL SERVIDOR DIÓ ERROR")
        else:
            enviar_seguro(tcpSocket, "ERROR")

# MAIN:
udpSocket = config_udp()
res = descubrir_server(udpSocket)

if res:
    IP_SERVIDOR, PUERTO_TCP, UMBRAL_CPU, UMBRAL_MEM = res
    tcpSocket = config_tcp(IP_SERVIDOR, PUERTO_TCP)

    buffer = b""
    registrado, buffer = registrar_agente(tcpSocket, buffer)

    if registrado:
        print("LISTO PARA COMENZAR MONITOREO")
        try:
            threading.Thread(target=monitorear, args=(tcpSocket,), daemon=True).start()
            enviar_procesos(tcpSocket, buffer)
        except KeyboardInterrupt:
            enviar_seguro(tcpSocket, "END")
        finally:
            tcpSocket.close()
    else:
        tcpSocket.close()