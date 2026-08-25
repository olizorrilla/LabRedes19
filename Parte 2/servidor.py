import socket
import threading

HOST = ""
PORT = 6019

# PREGUNTAR SI LO DEFINIMOS NOSTROS
UMBRAL_CPU = "80"
UMBRAL_MEM = "80"
PUERTO_TCP = "6020"
CLAVE = "clave_secreta"
ID_SIGUIENTE = 0 

agentes = {}
lock_ids = threading.Lock()

def config_udp():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) PREGUNTAR SI VA EN UDP
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
        datos, addr = udpSocket.recvfrom(2048) # PREGUNTAR POR TAMAÑO BUFFER
        mensaje = datos.decode()
        if mensaje == "DISCOVER\n":
            respuesta = f"SERVER {UMBRAL_CPU} {UMBRAL_MEM} {PUERTO_TCP}\n"
            udpSocket.sendto(respuesta.encode(), addr)

def atender_agente(conn, addr):
    global ID_SIGUIENTE
    datos = conn.recv(2048)
    mensaje = datos.decode()
    partes = mensaje.split()

    if (len(partes) == 2 and partes[0] == "REGISTER" and partes[1] == CLAVE):

        # SECCIÓN CRÍTICA para asignación de ids 
        with lock_ids:
            id_agente = ID_SIGUIENTE;
            ID_SIGUIENTE = ID_SIGUIENTE + 1
            agentes[id_agente] = {"addr": addr, "CPU": [], "MEM": []}

        conn.sendall("REG_RESP\n".encode())
        print(f"AGENTE REGISTRADO DESDE {addr}")
        print("AGENTES:", agentes)
        
    else:
        conn.sendall("ERROR\n".encode())

    conn.close()

udpSocket = config_udp()
tcpSocket = config_tcp()
threading.Thread(target=recibir_agente, args=(udpSocket,), daemon=True).start()
while True :
    conn, addr = tcpSocket.accept()
    threading.Thread(target=atender_agente, args=(conn, addr), daemon=True).start()