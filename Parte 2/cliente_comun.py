import socket
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

def config_udp():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return udpSocket

def config_tcp():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((IP_SERVIDOR, PUERTO_TCP))
    return tcp_socket

def descubrir_server(udpSocket):
    global UMBRAL_CPU, UMBRAL_MEM, PUERTO_TCP, IP_SERVIDOR
    udpSocket.sendto("DISCOVER\n".encode(), ('255.255.255.255', 6019)) # CAMBIAR POR ALGO DE LA SUBRED, NO ENTENDÍ

    datos, addr = udpSocket.recvfrom(2048)
    mensaje = datos.decode()
    partes = mensaje.split()

    print("MENSAJE RECIBIDO: ", mensaje, " DESDE: ", addr)

    if len(partes) == 4 and partes[0] == "SERVER":
        try:
            umbral_cpu = int(partes[1])
            umbral_mem = int(partes[2])
            puerto_tcp = int(partes[3])

            IP_SERVIDOR = addr[0]
            UMBRAL_CPU = umbral_cpu
            UMBRAL_MEM = umbral_mem
            PUERTO_TCP = puerto_tcp

            udpSocket.close()
            return True
        
        except ValueError:
            print("VALORES INCORRECTOS ENVIADOS POR EL SERVIDOR")
    else:
        print("RESPUESTA DEL SERVIDOR INCORRECTA")

    udpSocket.close()
    return False

def registrar_agente(tcpSocket, buffer):
    enviar_seguro(tcpSocket, f"REGISTER {CLAVE}")

    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)

    if respuesta == "REG_RESP":
        print("AGENTE REGISTRADO CORRECTAMENTE")
        return True, buffer
    
    print("NO SE PUDO REGISTRAR EL AGENTE")
    return False, buffer

def monitorear(tcpSocket):
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent

        enviar_seguro(tcpSocket, f"METRIC CPU {cpu}")
        enviar_seguro(tcpSocket, f"METRIC MEM {mem}")

        if cpu > UMBRAL_CPU:
            enviar_seguro(tcpSocket, f"ALERT CPU {cpu}")

        if mem > UMBRAL_MEM:
            enviar_seguro(tcpSocket, f"ALERT MEM {mem}")
        
        time.sleep(15)

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
descubierto = descubrir_server(udpSocket)

if descubierto:
    tcpSocket = config_tcp()

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