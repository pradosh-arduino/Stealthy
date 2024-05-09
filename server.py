#
#   Written by @pradosh-arduino on github
#


import socket
import signal
import threading
import json

HOST = ''
PORT = 0
MAX_MEMBERS = 0

buffer_size = 4096

# Dictionary to store client connections
clients = {}

# Extras
def color_text(text, color):
    colors = {
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'green': '\033[92m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'end': '\033[0m'
    }
    return f"{colors[color]}{text}{colors['end']}"

def error(message):
    print(color_text("[Error] " + message, 'red'))

def warn(message):
    print(color_text("[Warn] " + message, 'yellow'))

def info(message):
    print(color_text("[Info] " + message, 'blue'))
# End extras

def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False
    
def is_valid_port(port):
    try:
        return 0 < port <= 65535
    except ValueError:
        return False
    
def stop_server(signal, frame):
    broadcast("Server is stopping.")
    for client_socket in clients.values():
        client_socket.close()
    exit(0)

def handle_client(client_socket, username):
    while True:
        try:
            message = client_socket.recv(buffer_size).decode('utf-8')
            if message == '/quit':
                client_socket.close()
                del clients[username]
                broadcast(f'<font color=\'lightgrey\'>{username} has left the chat.</font>')
                break
            elif message == '/ping':
                broadcast('<font color=\'lightgrey\'>Pong!</font>')
            elif message == '/members':
                client_socket.sendall((str(list(clients.keys()))).encode())
            else:
                broadcast(f'{username}: {message}')
        except ConnectionResetError:
            client_socket.close()
            del clients[username]
            broadcast(f'<font color=\'lightgrey\'>{username} has left the chat.</font>')
            break
        except OSError:
            pass

def broadcast(message):
    try:
        for client_socket in clients.values():
            client_socket.send(message.encode('utf-8'))
    except Exception as e:
        error(f"Error broadcasting message: {e}")

def handle_commands(command):
    command = str(command)
    if command == "/quit":
        # stop_server(None, None)
        broadcast("Server is stopping.")
        for client_socket in clients.values():
            client_socket.close()
        info("Now its safe to press Ctrl+C")
        exit(0)
    elif command.startswith("/kick "):
        try:
            arg1 = command.split("/kick ")[1];
            clients[arg1].close()
        except KeyError:
            error("No member named as such to kick!")
    elif command == "/kick":
        error("Invalid command usage. (/kick <member-name>)")
    else:
        error("Invalid command passed, refer documents at <not yet>")

def command_threading():
    while True:
        cmd = input("")
        handle_commands(cmd)

def main():
    try:
        with open('defaults.json') as json_file:
            json_data = json.load(json_file)

        if json_data['ip'] == "localhost":
            HOST = "127.0.0.1"
        else:
            HOST = json_data['ip']
        
        PORT = json_data['port']

        MAX_MEMBERS = json_data['max-members']

        if not is_valid_ip(HOST):
            error("Not a valid IP has been saved in ./defaults.json!")
            exit(2)

        if not is_valid_port(PORT):
            error("Not a valid port has been saved in ./defaults.json!")
            exit(2)
        
        if not type(MAX_MEMBERS) == int:
            error("Not a valid member count has been saved in ./defaults.json!")
            exit(2)

        info("Loaded with ./defaults.json!")
    except FileNotFoundError:
        HOST = input("Enter the IP to host (localhost is also accepted) : ")
        if HOST == "localhost":
            HOST = '127.0.0.1'
    
        if not is_valid_ip(HOST):
            error("Not a valid IP has been entered!")
            exit(1)

        PORT = input("Enter server port                                 : ")
        PORT = int(PORT)
        if not is_valid_port(PORT):
            error("Not a valid port has been entered!")
            exit(1)

        MAX_MEMBERS = input("Enter maximum members allowed                     : ")
        try:
            MAX_MEMBERS = int(MAX_MEMBERS)
        except:
            error("Only integer is accepted for maximum members.")
            exit(3)

        
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((HOST, PORT))
    except:
        error("The address is already in use.")
        exit(4)
    
    server.listen()

    signal.signal(signal.SIGINT, stop_server)

    info(f'Server is listening on {HOST}:{PORT}')

    command_thread = threading.Thread(target=command_threading)
    command_thread.start()

    while True:
        if len(clients) > MAX_MEMBERS:
            # Server is full, reject new connections
            client_socket, _ = server.accept()
            client_socket.send("Server is full. Please try again later.".encode('utf-8'))
            client_socket.close()
            continue

        # Accept new connections
        client_socket, client_address = server.accept()
        info(f'New connection from {client_address[0]}:{client_address[1]}')

        username = client_socket.recv(buffer_size).decode('utf-8')
        clients[username] = client_socket

        broadcast(f'<font color=\'lightgrey\'>{username} has joined the chat.</font>')

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, username))
        client_thread.start()

if __name__ == "__main__":
    main()
