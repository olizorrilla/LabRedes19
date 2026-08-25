import socket

def config_cliente():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    clientSocket.sendto("DISCOVER\n".encode(), ('255.255.255.255', 6019))
    datos, adrr = clientSocket.recvfrom(2048)
    mensaje = datos.decode()
    print("Mensaje recibido:", mensaje)
    print("Desde:", adrr)
    # split, segun doc de python permite separar un mensaje estructurado en SERVER <> <> <> .. en partes[0] = SERVER, partes[1] = <> , ...
    partes = mensaje.split()
    if len(partes) == 4 and partes[0] == "SERVER":
        try:
            umbral_cpu = int(partes[1]) #si no logramos transformar cada uno de estos en un numero, entonces es incorrecto lo que mando el server
            umbral_mem = int(partes[2])
            puerto_tcp = int(partes[3])
        except ValueError:
            print("Respuesta del servidor incorrecta")
    #no se que deberia hacer si falla, falta ese caso del else 
    clientSocket.close()


config_cliente()