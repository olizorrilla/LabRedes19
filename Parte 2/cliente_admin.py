import psutil
import time
import threading
from aux import *

IP_SERVIDOR = None
PUERTO_TCP = None

CLAVE = "clave_secreta"

def registrar_admin(tcpSocket, buffer):
    enviar_mensaje(tcpSocket, f"ADMIN {CLAVE}")

    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)

    if respuesta == "ADMIN_RESP":
        print("ADMIN REGISTRADO CORRECTAMENTE")
        return True, buffer
    
    print("NO SE PUDO REGISTRAR EL AGENTE")
    return False, buffer

udpSocket = config_udp()
res = descubrir_server(udpSocket)

if res:
    IP_SERVIDOR, PUERTO_TCP, _, _ = res
    tcpSocket = config_tcp(IP_SERVIDOR, PUERTO_TCP)
