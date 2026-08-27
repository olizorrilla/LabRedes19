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

    