import socket
import threading

HOST = ""
PORT = 6019

# PREGUNTAR SI LO DEFINIMOS NOSTROS
UMBRAL_CPU = "80"
UMBRAL_MEM = "80"
PUERTO_TCP = "6020"

def config_server():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) PREGUNTAR SI VA EN UDP
    serverSocket.bind((HOST, PORT))
    return serverSocket


def recibir_agente(serverSocket):
    while True:
        datos, addr = serverSocket.recvfrom(2048) # PREGUNTAR POR TAMAÑO BUFFER
        mensaje = datos.decode() # strip() para eliminar \n
        if mensaje == "DISCOVER\n":
            respuesta = "SERVER " + UMBRAL_CPU + " " + UMBRAL_MEM + " " + PUERTO_TCP + "\n"

            serverSocket.sendto(
                respuesta.encode(),
                addr
            )

serverSocket = config_server()
recibir_agente(serverSocket)