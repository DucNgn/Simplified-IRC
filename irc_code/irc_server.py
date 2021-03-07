"""
SERVER SIDE IMPLEMENTATION 
"""

import socket
import sys, time
import argparse

import threading
import logging
import view
import common

logging.basicConfig(filename='view.log', level=logging.DEBUG)
logger = logging.getLogger()

"""
Class represents an user in the server.
"""
class user:
    def __init__(self, addr):
        self.registered = False
        self.addr = addr

    def set_username(self, username):
        self.username = username
        self.check_registered()

    def set_nickname(self, nickname):
        self.nickname = nickname
        self.check_registered()

    def join_channel(self, channel):
        self.channel = channel

    def check_registered(self):
        self.registered = hasattr(self, 'username') and hasattr(self, 'nickname') and self.joined()
        return self.registered

    def joined(self):
        return hasattr(self, 'channel')

"""
Class represents the server.
"""
class IRCServer():
    server = socket.socket()
    client_list = []
    online_users = []

    def __init__(self, HOST, PORT):
        self.HOST, self.PORT = HOST, PORT
        self.ADDR = (self.HOST, self.PORT)

        # Create and bind the server socket with the provided address.
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)

    """ 
    Method to start the server and listen to connections incoming from clients.
    """
    def start(self):
        self.server.listen()
        logger.info(f'[SERVER] Server is listening on {self.HOST} : {self.PORT}')
        while True:
            conn, addr = self.server.accept()
            self.client_list.append(conn)

            # Each client socket runs in a thread for concurrency between socket connections.
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()

            logger.info(f'[SERVER] Active connections: {len(self.client_list)}')
            logger.debug(f'[SERVER] Active threads: {threading.activeCount() - 1}')

        self.close()

    """
    Communicate with each client and take actions.
    """
    def handle_client(self, conn, addr):
        logger.info(f'[SERVER] New connection from client. {addr} connected.')
        connected = True
        while connected:
            msg_received = conn.recv(common.HEADER_SIZE).decode(common.ENCODE_FORMAT)
            if msg_received:
                connected = self.handle_data(conn, addr, msg_received)
        conn.close()

    """
    Handle the received data from a client.
    Return a boolean indicates if the connection should persist after handling.
    """
    def handle_data(self, conn, addr, msg):
        logger.info(f'[SERVER] received [{addr}] : {msg} ')
        print(f'[SERVER] [{addr}] {msg}')

        # Denote if current client profile is already created.
        connection_existed = any(u.addr == addr for u in self.online_users)

        if(msg.startswith('NICK ')): return self.handle_NICK(conn, addr, msg, connection_existed)

        # TODO: Extract information properly
        if(msg.startswith('USER ')):
            username = msg[len('USER '):]

            if connection_existed:
                for each_user in self.online_users:
                    if each_user.addr is addr:
                        each_user.set_username(username)
                        return True

            new_user = user(addr)
            new_user.set_username(username)
            self.online_users.append(new_user)
            return True

        if(msg.startswith('JOIN ')): return self.handle_JOIN(conn, addr, msg, connection_existed)

        # TODO: Handle this case using regex properly.
        if 'PRIVMSG' in msg:
            sender, _, content = common.extract_message(msg)
            prepare_msg = self.PRIVMSG(sender, content)
            self.broadcast(conn, addr, prepare_msg, False)
            return True

        if(msg.startswith('QUIT')): return self.handle_QUIT(conn, addr, msg)

        return True

    def PRIVMSG(self, sender, content):
        return f':{sender} PRIVMSG {common.CHANNEL} :{content}\n'

    """
    Broadcast a message server-wide.
    """
    def broadcast(self, conn, addr, msg, to_all=False):
        logger.info(f'[SERVER] Broadcasting message from {addr} to the whole server')
        for client_socket in self.client_list:
            if (client_socket is not conn) or to_all:
                print(f'[SERVER] Broadcasting: {msg}')
                client_socket.send(bytes(msg, common.ENCODE_FORMAT))

    """
    Close all openning sockets.
    """
    def close(self):
        for s in self.client_list:
            s.close()
        self.server.close()

    """
    Set of functions to handle requests from client in RFC 1459 format
    """

    def handle_NICK(self, conn, addr, msg, connection_existed):
        nickname = msg[len('NICK '):]

        if connection_existed:
            for each_user in self.online_users:
                if each_user.addr is addr:
                    each_user.set_nickname(nickname)
                    return True

        new_user = user(addr)
        new_user.set_nickname(nickname)
        self.online_users.append(new_user)
        return True

    def handle_JOIN(self, conn, addr, msg, connection_existed):
        channel = msg[len('JOIN '):]

        if connection_existed:
            for each_user in self.online_users:
                if each_user.addr is addr:
                    each_user.join_channel(channel)
                    if each_user.check_registered():
                        self.broadcast(conn, addr, self.PRIVMSG('SERVER', f'Welcome {each_user.nickname} to our amazing channel\n'), to_all=True)
                    return True

        new_user = user(addr)
        new_user.join_channel(channel)
        self.online_users.append(new_user)
        return True

    def handle_QUIT(self, conn, addr, msg):
        self.client_list.remove(conn)
        self.broadcast(conn, addr, msg.split(':', 1)[1])
        return False

    """
    End of domain
    """

def main(args):
    # HOST = socket.gethostbyname(socket.gethostname())
    HOST = ''
    PORT = args.port
    try:
        server = IRCServer(HOST, PORT)
        server.start()
    except KeyboardInterrupt:
        logger.info(f'[SERVER] Keyboard interrupted server. Server is terminating')
        server.close()
        sys.exit()

if __name__ == '__main__':
    # TODO: Pass arguments properly here
    # create parser object
    parser = argparse.ArgumentParser(description="This is the irc client")

    # defining arguments for parser object
    parser.add_argument("-p", "--port", type=str, nargs=1,
                        metavar="PORT", default=5050,
                        help="Target port to use")

    # parse the arguments from standard input
    args = parser.parse_args()
    print(args)
    main(args)