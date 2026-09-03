import socket
import psutil
import ipaddress

def config_udp():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return udpSocket

def config_tcp(ip_servidor, puerto_tcp):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((ip_servidor, puerto_tcp))
    return tcp_socket

def seleccionar_interfaz():
    interfaces = psutil.net_if_addrs()
    interfaces_validas = []

    for nombre, direcciones in interfaces.items():
        for direccion in direcciones:
            if direccion.family != socket.AF_INET:
                continue

            interfaces_validas.append((nombre, direccion.address, direccion.netmask))
            break

    if len(interfaces_validas) == 0:
        print("NO SE ENCONTRARON INTERFACES IPv4 VÁLIDAS")
        return None

    print("INTERFACES DISPONIBLES:")
    for numero, interfaz in enumerate(interfaces_validas, start=1):
        nombre, direccion_ip, mascara = interfaz
        print(f"{numero}. {nombre} - IP: {direccion_ip} - MÁSCARA: {mascara}")

    while True:
        try:
            numero_elegido = int(input("SELECCIONE UNA INTERFAZ: "))
        except ValueError:
            print("DEBE INGRESAR UN NÚMERO")
            continue

        if numero_elegido < 1 or numero_elegido > len(interfaces_validas):
            print("EL NÚMERO DE INTERFAZ NO ES VÁLIDO")
            continue

        nombre_interfaz, direccion_ip, mascara = interfaces_validas[numero_elegido - 1]
        return nombre_interfaz, direccion_ip, mascara

def obtener_broadcast_lan(nombre_interfaz, direccion_ip, mascara):
    red = ipaddress.IPv4Network(f"{direccion_ip}/{mascara}", strict=False)

    print("INTERFAZ SELECCIONADA:", nombre_interfaz)
    print("DIRECCIÓN IPv4:", direccion_ip)
    print("MÁSCARA:", mascara)
    print("BROADCAST CALCULADO:", red.broadcast_address)

    return str(red.broadcast_address)

def descubrir_server(udpSocket):
    try:
        interfaz = seleccionar_interfaz()

        if interfaz is None:
            return False

        nombre_interfaz, direccion_ip, mascara = interfaz

        broadcast = obtener_broadcast_lan(nombre_interfaz, direccion_ip, mascara)

        if broadcast is None:
            print("NO SE PUDO OBTENER EL BROADCAST DE LA RED")
            return False

        udpSocket.sendto("DISCOVER\n".encode(), (broadcast, 6019))

        datos, addr = udpSocket.recvfrom(2048)
        mensaje = datos.decode()
        partes = mensaje.split()

        print("MENSAJE RECIBIDO: ", mensaje, " DESDE: ", addr)

        if len(partes) != 4 or partes[0] != "SERVER":
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

    