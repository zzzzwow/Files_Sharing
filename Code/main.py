import hashlib
import os.path
import threading
import time
import sys
import base


class Args:
    def __init__(self):
        self.ip = sys.argv[2]
        # store command line parameters in sys.argv
        # 2:to return the third parameter ip address (script name, --ip, the value of ip address)


def file_hash(file):
    """
    calculates the hash value of the file
    :param file:
    :return: md5.hexdigest()
    """
    md5 = hashlib.md5()
    for chunk in read_file(file):
        md5.update(chunk)  
    return md5.hexdigest()


def find_all_files(path="share"):
    """
    find all files in 'share'
    :param path:
    :return: root,file
    """
    for root, dirs, files in os.walk(path):
        # os.walk() is recursive
        # Os. walk() walks through all the files in the share folder here
        # returning root: the share folder itself
        # dirs:The names of all directories in this folder  files:All files in this folder
        for file in files: # os.walk() is recursive
            yield os.path.join(root, file)  # Here the Topdown of os.walk is True by default


def folder_dict(files):
    """
    Generate folder dictionary {filename, hash value}
    :param files:
    :return: data
    """
    data = {}
    for file in files:
        data[file] = file_hash(file)
    return data


def compare(a, b):
    """
    Compare the differences between two dictionaries
    :param a:
    :param b:
    :return: data
    """
    keys = b.keys()
    data = {}
    for k, v in a.items():
        if k not in keys:  # files in a, but not in b
            print("ADD", k)
            data[k] = "add"
        elif k in keys:
            if v != b[k]:  # files in a, b but have different content
                print("DIFFERENCE", k)
                data[k] = "update"
    return data


def send_file(sock, file):
    size = os.path.getsize(file)
    data = {'code': 0, "content": {"file": file, "size": size}}
    print(data)
    base.send_message(sock, data)
    for block in read_file(file):
        sock.send(block)


def send_all_file(sock, files):
    """
    Send all files in the folder
    :param sock:
    :param files:
    :return:
    """
    for file in files:
        print(file)
        send_file(sock, file)


def read_file(file):
    with open(file, 'rb') as fp:
        while True:
            block = fp.read(base.CHUNK)
            if not block:
                break
            yield block


def make_dirs(path):
    """
    recursively create directories extract file names from directories
    :param path:
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)


def recv_all_files(sock):
    while True:
        message = base.recv_message(sock)
        print("message:", message)
        if message['code'] == -1:
            print("stop")
            break
        filename = message['content']['file']
        path, name = os.path.split(filename)
        make_dirs(path)
        size = message['content']['size']
        with open(filename, 'wb') as fp:
            for chunk in base.recv_chunk(sock, size):
                fp.write(chunk)

# the first method
def client_handle(client, address):
    print("client", address)
    server_folder_dict = None
    try:
        while True:
            message = base.recv_message(client)  # accept the request message
            if message['code'] == 1:
                # After the connection is established, the server sends all files to the client
                send_all_file(client, find_all_files("share/"))
            elif message['code'] == 2:  # The current method does not execute to 2
                client_folder_dict = message['content']
                server_folder_dict = folder_dict(find_all_files("share/"))
                new_info = compare(server_folder_dict, client_folder_dict)  # the difference between two dictionaries
                send_all_file(client, new_info.keys())
            base.send_message(client, {'code': -1})  # ending file Transfer
            break
    except OSError as e:
        print(e)
    else:
        if server_folder_dict is not None:
            info = {"code": 2, "content": server_folder_dict}
        else:
            info = {"code": 1}
        print("A request file", info)
        threading.Timer(3, run_client, args=(args.ip, info)).start()
    finally:
        client.close()


# the second method
# def client_handle(client, address):
#     print("client", address)
#     server_folder_dict = None
#     try:
#         while True:
#             message = base.recv_message(client)  # accept the request message
#             if message['code'] == 1:
#                 send_all_file(client, find_all_files("share/"))  # send all files
#             if message['code'] == 2:
#                 client_folder_dict = message['content']  # a dictionary of received client folder information
#                 server_folder_dict = folder_dict(find_all_files("share/"))  # generate a server folder dictionary
#                 new_info = compare(server_folder_dict, client_folder_dict)  # comparing folder differences
#                 send_all_file(client, new_info.keys())  # server sends the extracted file to the client after comparison
#             base.send_message(client, {'code': -1})  # ending file Transfer
#             break
#     except OSError as e:
#         print(e)
#     else:
#         if server_folder_dict is None:
#             server_folder_dict = folder_dict(find_all_files("share/"))
#             info = {"code": 2, "content": server_folder_dict}
#         else:
#             info = {"code": 2, "content": folder_dict(find_all_files("share/"))}
#         print("A request file", info)
#         threading.Timer(3, run_client, args=(args.ip, info)).start()  # The timer is set to 3s
#     finally:
#         client.close()  # the client closes the connection


def run_server():
    sock = base.server()
    print("start my server")
    while True:
        print("start wait client connect...")
        client, address = sock.accept()
        print('connect success')
        threading.Thread(target=client_handle, args=(client, address)).start()
        # the thread here is used to maintain a client connection


def request_file(sock, data):
    base.send_message(sock, data=data)


def run_client(ip, data):
    try:
        sock = base.client(ip)
        start = time.time()
        request_file(sock, data)
        recv_all_files(sock)
        print("transport file use: %s seconds" % (time.time() - start))

    except OSError as e:
        print("client recv close!!!", ip, e)


if __name__ == '__main__':
    args = Args()
    data = {"code": 1}  # code = 1 Request all files
    run_client(args.ip, data)
    print("end", args.ip)
    run_server()

