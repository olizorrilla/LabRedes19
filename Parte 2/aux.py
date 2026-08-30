import psutil
import socket

def obtener_broadcast_lan():
    interfaces = psutil.net_if_addrs() # devuelve por cada interfaz su clave (el nombre wifi/ethernet/lo) y una lista de direcciones asociadas (ipv4, ipv6, MAC)

    for nombre, direcciones in interfaces.items():
        if nombre == "lo":          # salteo loopback
            continue
        for direccion in direcciones:
            if direccion.family == socket.AF_INET and direccion.broadcast: # cada direccion tiene 5 campos, filtro solo las que el campo family sea ipv4
                return direccion.broadcast
    return None  # no se encontró ninguna interfaz con broadcast

def config_udp():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return udpSocket

def config_tcp(ip_servidor, puerto_tcp):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((ip_servidor, puerto_tcp))
    return tcp_socket

def descubrir_server(udpSocket):
    try:
        broadcast = obtener_broadcast_lan()
        udpSocket.sendto("DISCOVER\n".encode(), (broadcast, 6019))

        datos, addr = udpSocket.recvfrom(2048)
        mensaje = datos.decode()
        partes = mensaje.split()

        print("MENSAJE RECIBIDO: ", mensaje, " DESDE: ", addr)

        if len(partes) != 4 or partes[0] != "SERVER": # habría que chequear si nos mando numeros validos? por ej, puerto con coma o umbral mayor a 100 o menor que 0
            print("RESPUESTA DEL SERVIDOR INCORRECTA")
            return False

        try:
            umbral_cpu = int(partes[1])
            umbral_mem = int(partes[2])
            puerto_tcp = int(partes[3])
        except ValueError:
            print("LOS VALORES ENVIADOS POR EL SERVIDOR SON INCORRECTOS")
            return False

        ip_servidor = addr[0]
        return ip_servidor, puerto_tcp, umbral_cpu, umbral_mem
        
    finally:
        udpSocket.close()

def enviar_mensaje(tcpSocket, mensaje):
    datos = f"{mensaje}\n".encode()

    while datos != b"": # b"" ES "" PERO EN BYTES
        cantidad_enviada = tcpSocket.send(datos)

        if cantidad_enviada == 0:
            raise ConnectionError("LA CONEXIÓN FUE CERRADA") # EXCEPCIÓN POR SI SE CORTA LA CONEXIÓN
        
        datos = datos[cantidad_enviada:]

def recibir_mensaje(tcpSocket, buffer):
    while b"\n" not in buffer:
        datos_recibidos = tcpSocket.recv(2048)

        if datos_recibidos == b"":
            raise ConnectionError("LA CONEXIÓN FUE CERRADA")

        buffer += datos_recibidos

    pos = buffer.find(b"\n")

    mensaje_bytes = buffer[:pos]
    buffer = buffer[pos + 1:]

    mensaje = mensaje_bytes.decode()

    return mensaje, buffer

    