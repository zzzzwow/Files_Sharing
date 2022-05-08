import socket
import struct

PORT = 20001
CHUNK = 15364


def create():
    """
    create socket
    :return: server_socket
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return server_socket


def server(listen=5):
    sock = create()
    sock.bind(("0.0.0.0", PORT))
    sock.listen(listen)  # Set the maximum number of connections to 5
    return sock


def client(ip):
    sock = create()
    sock.connect((ip, PORT))
    return sock


def send_message(sock, data):
    content = str(data).encode('utf-8')
    sock.send(struct.pack(">i", len(content)) + content)


def recv_chunk(sock, size, chunk=CHUNK):
    while size > 0:
        chunk = size if chunk > size else chunk
        block = sock.recv(chunk)
        size -= len(block)
        yield block


def recv_message(sock):
    """
    accepts header information for any type of file
    """
    length = b"".join(recv_chunk(sock, size=4))
    length = struct.unpack(">i", length)[0]
    content = b''.join(recv_chunk(sock, length))
    return eval(content)  # Convert to the original type using eval()
    # return a dictionary
