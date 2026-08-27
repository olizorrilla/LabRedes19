import socket
import threading
from aux import *

HOST = ""
PORT = 6019

UMBRAL_CPU = "80"
UMBRAL_MEM = "80"
PUERTO_TCP = "6020"

CLAVE = "clave_secreta"

agentes = {}

def config_udp():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.bind((HOST, PORT))
    return udpSocket

def config_tcp():
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpSocket.bind((HOST, int(PUERTO_TCP)))
    tcpSocket.listen()
    return tcpSocket

def recibir_agente(udpSocket):
    while True:
        datos, addr = udpSocket.recvfrom(2048)
        mensaje = datos.decode()
        if mensaje == "DISCOVER\n":
            respuesta = f"SERVER {UMBRAL_CPU} {UMBRAL_MEM} {PUERTO_TCP}\n"
            udpSocket.sendto(respuesta.encode(), addr)

def atender_agente(tcpSocket, addr):
    buffer = b""

    try:
        mensaje, buffer = recibir_mensaje(tcpSocket, buffer)
        partes = mensaje.split()

        if (len(partes) == 2 and partes[0] == "REGISTER" and partes[1] == CLAVE):
            agentes[addr] = {"CPU": [], "MEM":[]}
            enviar_mensaje(tcpSocket, "REG_RESP")
            print(f"AGENTE REGISTRADO DESDE {addr}")

            while True: # ACA VA MONITOREO
                    mensaje, buffer = recibir_mensaje(tcpSocket, buffer)

                    if mensaje == "END": # QUE CORTÓ LA CONEXIÓN, CAPAZ HAY QUE MOSTRAR ALGO
                        break

                    print(f"RECIBIDO DESDE {addr}: {mensaje}")

        else:
            enviar_mensaje(tcpSocket, "ERROR")

    except ConnectionError:
        print("CONEXIÓN CERRADA")
    
    tcpSocket.close()

udpSocket = config_udp()
tcpSocket = config_tcp()
threading.Thread(target=recibir_agente, args=(udpSocket,), daemon=True).start()
while True :
    conn, addr = tcpSocket.accept()
    threading.Thread(target=atender_agente, args=(conn, addr), daemon=True).start()