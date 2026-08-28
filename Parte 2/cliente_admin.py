import socket
import psutil
import time
import threading
from aux import *

IP_SERVIDOR = None
PUERTO_TCP = None

CLAVE = "clave_secreta"

def config_udp():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return udpSocket

def config_tcp():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((IP_SERVIDOR, PUERTO_TCP))
    return tcp_socket

def descubrir_server(udpSocket):
    global PUERTO_TCP, IP_SERVIDOR
    udpSocket.sendto("DISCOVER\n".encode(), ('255.255.255.255', 6019)) # CAMBIAR POR ALGO DE LA SUBRED, NO ENTENDÍ

    datos, addr = udpSocket.recvfrom(2048)
    mensaje = datos.decode()
    partes = mensaje.split()

    print("MENSAJE RECIBIDO: ", mensaje, " DESDE: ", addr)

    if len(partes) == 4 and partes[0] == "SERVER":
        try:
            puerto_tcp = int(partes[3])
            IP_SERVIDOR = addr[0]
            PUERTO_TCP = puerto_tcp

            udpSocket.close()
            return True
        
        except ValueError:
            print("VALORES INCORRECTOS ENVIADOS POR EL SERVIDOR")
    else:
        print("RESPUESTA DEL SERVIDOR INCORRECTA")

    udpSocket.close()
    return False

def registrar_admin(tcpSocket, buffer):
    enviar_mensaje(tcpSocket, f"ADMIN {CLAVE}")

    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)

    if respuesta == "ADMIN_RESP":
        print("ADMIN REGISTRADO CORRECTAMENTE")
        return True, buffer
    
    print("NO SE PUDO REGISTRAR EL AGENTE")
    return False, buffer
