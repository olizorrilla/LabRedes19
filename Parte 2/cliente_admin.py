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

    buffer = b""
    registrado, buffer = registrar_admin(tcpSocket, buffer)

    if registrado:
        print("LISTO PARA COMENZAR")
        print()
        print("COMANDOS DISPONIBLES:")
        print(" L               -> Lista los agentes conectados.") 
        print(" M <x> <CPU|MEM> -> Consulta una métrica del agente x.")
        print(" P               -> Consulta los procesos del agente x.")
        print(" END             -> Cierra la conexión.")
        print(" SUGERENCIA: Primero utilice L para obtener los agentes.")

        ids_agentes = []

        try:
            while True:
                entrada = input("> ").strip()
                partes = entrada.split()
                
                if entrada == "END":
                    enviar_mensaje(tcpSocket, "END")
                    break

                elif entrada == "L":
                    enviar_mensaje(tcpSocket, "LIST_AGENTS")
                    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)
                    print(respuesta)

                    partes_respuesta = respuesta.split()
                    ids_agentes = partes_respuesta[2:]

                elif len(partes) == 3 and partes[0] == "M":
                    # CASO M
                    pass

                elif len(partes) == 2 and partes[0] == "P":
                    # CASO P
                    pass

                else:
                    print("COMANDO INVÁLIDO")
        except ConnectionAbortedError:
            print("SE PERDIÓ LA CONEXIÓN CON EL SERVIDOR")
        except KeyboardInterrupt:
            enviar_mensaje(tcpSocket, "END")
        finally:
            tcpSocket.close()
    else:
        tcpSocket.close()
