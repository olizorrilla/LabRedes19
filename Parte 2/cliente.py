import socket

UMBRAL_CPU = None
UMBRAL_MEM = None
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
    global UMBRAL_CPU, UMBRAL_MEM, PUERTO_TCP, IP_SERVIDOR
    udpSocket.sendto("DISCOVER\n".encode(), ('255.255.255.255', 6019))

    datos, adrr = udpSocket.recvfrom(2048)
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

            udpSocket.close()
            return True
        
        except ValueError:
            print("VALORES INCORRECTOS ENVIADOS POR EL SERVIDOR")
    else:
        print("RESPUESTA DEL SERVIDOR INCORRECTA")

    udpSocket.close()
    return False

def registrar_agente(tcpSocket):
    mensaje = f"REGISTER {CLAVE}\n"
    tcpSocket.sendall(mensaje.encode()) # PREGUNTAR SENDALL, SI NO ES NECESARIO UN BUCLE

    respuesta = tcpSocket.recv(2048).decode()

    if respuesta == "REG_RESP\n":
        print("AGENTE REGISTRADO CORRECTAMENTE")
        return True
    
    print("NO SE PUDO REGISTRAR EL AGENTE")
    return False

udpSocket = config_udp()
descubierto = descubrir_server(udpSocket)

if descubierto:
    tcpSocket = config_tcp()

    if registrar_agente(tcpSocket):
        print("LISTO PARA COMENZAR MONITOREO")
    else:
        tcpSocket.close()