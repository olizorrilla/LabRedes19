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

def obtener_agentes(tcpSocket, buffer, mostrar):
    enviar_mensaje(tcpSocket, "LIST_AGENTS")
    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)

    partes_respuesta = respuesta.split()

    if len(partes_respuesta) < 2 or partes_respuesta[0] != "AGENTS":
        print("RESPUESTA INCORRECTA DEL SERVIDOR")
        return [], buffer

    try:
        cantidad = int(partes_respuesta[1])
    except ValueError:
        print("RESPUESTA INCORRECTA DEL SERVIDOR")
        return [], buffer

    ids_agentes = partes_respuesta[2:]

    if cantidad != len(ids_agentes):
        print("RESPUESTA INCORRECTA DEL SERVIDOR")
        return [], buffer

    if mostrar:
        if cantidad == 0:
            print("NO HAY AGENTES CONECTADOS")
        else:
            print("AGENTES CONECTADOS:")
            for numero, id_agente in enumerate(ids_agentes, start=1):
                print(f"{numero} - {id_agente}")

    return ids_agentes, buffer

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
        print(" P <x>           -> Consulta los procesos del agente x.")
        print(" END             -> Cierra la conexión.")

        ids_agentes = []

        try:
            while True:
                entrada = input("> ").strip()
                partes = entrada.split()
                
                if entrada == "END":
                    enviar_mensaje(tcpSocket, "END")
                    break

                elif entrada == "L":
                    ids_agentes, buffer = obtener_agentes(tcpSocket, buffer, True)

                elif len(partes) == 3 and partes[0] == "M":
                    try:
                        numero_agente = int(partes[1])
                    except ValueError:
                        print("EL NÚMERO DEL AGENTE DEBE SER UN ENTERO")
                        continue

                    nombre_metrica = partes[2]

                    if nombre_metrica != "CPU" and nombre_metrica != "MEM":
                        print("LA MÉTRICA DEBE SER CPU O MEM")
                        continue

                    ids_agentes, buffer = obtener_agentes(tcpSocket, buffer, False)

                    if numero_agente < 1 or numero_agente > len(ids_agentes):
                        print("EL NÚMERO DE AGENTE NO ES VÁLIDO")
                        continue

                    id_agente = ids_agentes[numero_agente - 1] # -1 PORQUE LAS LISTAS COMIENZAN EN 0
                    enviar_mensaje(tcpSocket, f"GET_METRIC {id_agente} {nombre_metrica}")

                    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)
                    partes_respuesta = respuesta.split()

                    if respuesta == "ERROR":
                        print("EL SERVIDOR NO PUDO REALIZAR LA CONSULTA")

                    elif len(partes_respuesta) >= 4 and partes_respuesta[0] == "MEASUREMENTS":
                        id_respuesta = partes_respuesta[1]
                        metrica_respuesta = partes_respuesta[2]

                        try:
                            cantidad = int(partes_respuesta[3])
                        except ValueError:
                            print("RESPUESTA INCORRECTA DEL SERVIDOR")
                            continue

                        valores = partes_respuesta[4:]

                        if cantidad != len(valores):
                            print("RESPUESTA INCORRECTA DEL SERVIDOR")
                            continue

                        if cantidad == 0:
                            print(f"EL AGENTE {numero_agente} TODAVÍA NO TIENE MEDICIONES DE {metrica_respuesta}")
                        else:
                            print(f"MEDICIONES DE {metrica_respuesta} DEL AGENTE {numero_agente}:")
                            for numero, valor in enumerate(valores, start=1):
                                print(f"{numero} - {valor}")
                    else:
                        print("RESPUESTA INCORRECTA DEL SERVIDOR")

                elif len(partes) == 2 and partes[0] == "P":
                    try:
                        numero_agente = int(partes[1])
                    except ValueError:
                        print("EL NÚMERO DEL AGENTE DEBE SER UN ENTERO")
                        continue

                    ids_agentes, buffer = obtener_agentes(tcpSocket, buffer, False)

                    if numero_agente < 1 or numero_agente > len(ids_agentes):
                        print("EL NÚMERO DE AGENTE NO ES VÁLIDO")
                        continue

                    id_agente = ids_agentes[numero_agente - 1]
                    enviar_mensaje(tcpSocket, f"GET_PROC {id_agente}")

                    respuesta, buffer = recibir_mensaje(tcpSocket, buffer)

                    if respuesta == "ERROR":
                        print("EL SERVIDOR NO PUDO REALIZAR LA CONSULTA")
                        continue

                    partes_respuesta = respuesta.split(maxsplit=2) # MAXSPLIT UTILIZA COMO MAXIMO DOS PARTICIONES, NOS QUEDA PROC / ID / LISTA_PROCESOS

                    if len(partes_respuesta) == 3 and partes_respuesta[0] == "PROC" and partes_respuesta[1] == id_agente:    
                        procesos = partes_respuesta[2]

                        print(f"PROCESOS DEL AGENTE {numero_agente}:")

                        for proceso in procesos.split(", "):
                            pid, separador, nombre = proceso.partition(":")

                            if separador == "":
                                print(proceso)
                            else:
                                print(f"{pid} - {nombre}")

                    else:
                        print("RESPUESTA INCORRECTA DEL SERVIDOR")
                    
                else:
                    print("COMANDO INVÁLIDO")
        except ConnectionError:
            print("SE PERDIÓ LA CONEXIÓN CON EL SERVIDOR")
        except KeyboardInterrupt:
            enviar_mensaje(tcpSocket, "END")
        finally:
            tcpSocket.close()
    else:
        tcpSocket.close()
