import socket

UMBRAL_CPU = None
UMBRAL_MEM = None
PUERTO_TCP = None
IP_SERVIDOR = None

def config_cliente():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return clientSocket

def descubrir_server(clientSocket):
    global UMBRAL_CPU, UMBRAL_MEM, PUERTO_TCP, IP_SERVIDOR
    clientSocket.sendto("DISCOVER\n".encode(), ('255.255.255.255', 6019))

    datos, adrr = clientSocket.recvfrom(2048)
    mensaje = datos.decode()
    partes = mensaje.split() # SPLIT: SEPARA SERVER <> <> <> .. EN PARTES[0] = SERVER, PARTES[1] = <>, ...


    #PARA TESTEO:
    print("Mensaje recibido:", mensaje)
    print("Desde:", adrr)

    if len(partes) == 4 and partes[0] == "SERVER":
        try:
            umbral_cpu = int(partes[1])
            umbral_mem = int(partes[2])
            puerto_tcp = int(partes[3])

            # ASIGNO A VARIABLES GLOBALES
            IP_SERVIDOR = adrr[0]
            UMBRAL_CPU = umbral_cpu
            UMBRAL_MEM = umbral_mem
            PUERTO_TCP = puerto_tcp
        except ValueError:
            print("VALORES INCORRECTOS ENVIADOS POR EL SERVIDOR")
    else:
        print("RESPUESTA DEL SERVIDOR INCORRECTA")
    clientSocket.close()


clientSocket = config_cliente()
descubrir_server(clientSocket)