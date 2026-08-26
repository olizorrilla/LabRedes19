import socket
import psutil
import time

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
    udpSocket.sendto("DISCOVER\n".encode(), ('255.255.255.255', 6019)) # CAMBIAR POR ALGO DE LA SUBRED, NO ENTENDÍ

    datos, addr = udpSocket.recvfrom(2048)
    mensaje = datos.decode()
    partes = mensaje.split()

    #PARA TESTEO:
    print("MENSAJE RECIBIDO: ", mensaje, " DESDE: ", addr)

    if len(partes) == 4 and partes[0] == "SERVER":
        try:
            umbral_cpu = int(partes[1])
            umbral_mem = int(partes[2])
            puerto_tcp = int(partes[3])

            # ASIGNO A VARIABLES GLOBALES
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

def registrar_agente(tcpSocket):
    mensaje = f"REGISTER {CLAVE}\n"
    tcpSocket.sendall(mensaje.encode()) # CAMBIAR POR BUCLE

    respuesta = tcpSocket.recv(2048).decode()

    if respuesta == "REG_RESP\n":
        print("AGENTE REGISTRADO CORRECTAMENTE")
        return True
    
    print("NO SE PUDO REGISTRAR EL AGENTE")
    return False

def monitorear(tcpSocket):
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent

        tcpSocket.sendall(f"METRIC CPU {cpu}\n".encode()) # CAMBIAR POR BUCLE
        tcpSocket.sendall(f"METRIC MEM {mem}\n".encode()) # CAMBIAR POR BUCLE

        if cpu > UMBRAL_CPU:
            tcpSocket.sendall(f"ALERT CPU {cpu}\n".encode()) # CAMBIAR POR BUCLE

        if mem > UMBRAL_MEM:
            tcpSocket.sendall(f"ALERT MEM {mem}\n".encode()) # CAMBIAR POR BUCLE
        
        time.sleep(15)

udpSocket = config_udp()
descubierto = descubrir_server(udpSocket)

if descubierto:
    tcpSocket = config_tcp()

    if registrar_agente(tcpSocket):
        print("LISTO PARA COMENZAR MONITOREO")
        try:
            monitorear(tcpSocket)
        except KeyboardInterrupt:
            tcpSocket.sendall(b"END\n") # CAMBIAR POR BUCLE
        finally:
            tcpSocket.close()
    else:
        tcpSocket.close()