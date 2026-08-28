import socket
import threading
from aux import enviar_mensaje, recibir_mensaje

HOST = ""
PORT = 6019

UMBRAL_CPU = "80"
UMBRAL_MEM = "80"
PUERTO_TCP = "6020"

CLAVE = "clave_secreta"

lock_agentes = threading.Lock()
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
    id_agente = None

    try:
        mensaje, buffer = recibir_mensaje(tcpSocket, buffer)
        partes = mensaje.split()

        # AGENTE COMUN:
        if len(partes) == 2 and partes[0] == "REGISTER" and partes[1] == CLAVE:
            id_agente = f"{addr[0]}:{addr[1]}"
            with lock_agentes:
                agentes[id_agente] = {"Dir": addr, "Socket": tcpSocket, "CPU": [], "MEM": []} # GUARDO EL SOCKET Y ADDR PARA IDENTIFICARLO CUANDO TENGA QUE RESPONDER LA SOLICITUD DEL ADMIN

            enviar_mensaje(tcpSocket, "REG_RESP")
            print(f"AGENTE REGISTRADO DESDE {addr}")

            while True:
                mensaje, buffer = recibir_mensaje(tcpSocket, buffer)
                print(f"RECIBIDO DESDE {addr}: {mensaje}")
                partes = mensaje.split()

                # LÓGICA CORTAR CONEXIÓN: // LIBERAR agentes[]
                if mensaje == "END":
                    break

                # LÓGICA REGISTRO ÚLTIMAS 10 MÉTRICAS:
                if len(partes) == 3 and partes[0] == "METRIC":
                    nombre_metrica = partes[1]
                    try: # PARA VERIFICAR POR MENSAJE DEL TIPO METRIC CPU hola
                        valor = float(partes[2])
                    except ValueError:
                        enviar_mensaje(tcpSocket, "ERROR")
                        continue # VUELVE AL COMIENZO DEL WHILE

                    if nombre_metrica == "CPU" or nombre_metrica == "MEM":
                        with lock_agentes:
                            agentes[id_agente][nombre_metrica].append(valor)

                            if len(agentes[id_agente][nombre_metrica]) > 10:
                                agentes[id_agente][nombre_metrica].pop(0)
                    else:
                        enviar_mensaje(tcpSocket, "ERROR")
                        continue

                # LÓGICA MANEJO ALERTAS: 
                elif len(partes) == 3 and partes[0] == "ALERT":
                    pass

                # LÓGICA RECIBIMIENTO PROCESOS CORRIENDO:
                elif mensaje.startswith("PROC "):
                    procesos = mensaje[len("PROC "):]
                    print(f"PROCESOS DE {id_agente}:{procesos}")
                    # aca en realidad hay que identificar a que admin mandarle esta info
                
                elif mensaje == "ERROR":
                    print(f"EL AGENTE {id_agente} INFORMÓ UN ERROR")

                else:
                    enviar_mensaje(tcpSocket, "ERROR")
        
        # AGENTE ADMIN
        elif len(partes) == 2 and partes[0] == "ADMIN" and partes[1] == CLAVE:
            enviar_mensaje(tcpSocket, "ADMIN_RESP")
            print(f"ADMIN REGISTRADO DESDE {addr}")

            while True:
                mensaje, buffer = recibir_mensaje(tcpSocket, buffer)

                if mensaje == "END": # QUE CORTÓ LA CONEXIÓN
                    break

        # ERROR:
        else:
            enviar_mensaje(tcpSocket, "ERROR")

    except ConnectionError:
        print("CONEXIÓN CERRADA")

    finally: # FINALLY ES UNA PARTE DEL TRY QUE SE EJECUTA SIEMPRE
        if id_agente is not None:
            with lock_agentes:
                agentes.pop(id_agente, None)

            print(f"AGENTE {id_agente} ELIMINADO")
        tcpSocket.close()
    

udpSocket = config_udp()
tcpSocket = config_tcp()
threading.Thread(target=recibir_agente, args=(udpSocket,), daemon=True).start()
while True :
    conn, addr = tcpSocket.accept()
    threading.Thread(target=atender_agente, args=(conn, addr), daemon=True).start()