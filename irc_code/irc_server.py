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
import select

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
        self.check_registered()

    def check_registered(self):
        # User is registered successfully if the profile has username, nickname, and joined a channel.
        self.registered = hasattr(self, 'username') and hasattr(self, 'nickname') and hasattr(self, 'channel')
        return self.registered

"""
Class represents the server.
"""
class IRCServer():
    server_socket = socket.socket()
    online_users = []
    SOCKET_LIST = []

    def __init__(self, HOST, PORT):
        """ Initialize the server """
        self.HOST, self.PORT = HOST, PORT
        self.ADDR = (self.HOST, self.PORT)

        # Create and bind the server socket with the provided address.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.ADDR)
        self.server_socket.setblocking(False)

    def start(self):
        """ Method to start the server and listen to connections incoming from clients. """
        self.server_socket.listen()
        self.SOCKET_LIST.append(self.server_socket)

        while True:
            ready_to_read, _, _ = select.select(self.SOCKET_LIST, [], [], 0)

            for sock in ready_to_read:
                # New connection request.
                if sock is self.server_socket:
                    sockfd, _ = self.server_socket.accept()
                    self.SOCKET_LIST.append(sockfd)

                # A message from client to server
                else:
                    try:
                        data = sock.recv(common.HEADER_SIZE).decode(common.ENCODE_FORMAT)
                        if data:
                            self.handle_data(sock, data)
                        else:
                            if sock in self.SOCKET_LIST:
                                self.SOCKET_LIST.remove(sock)
                    except:
                        self.broadcast(sock, f'Client out of the server')
                        print('Client offline')
                        continue
        self.server_socket.close()


    """
    Handle the received data from a client.
    """
    def handle_data(self, conn, msg):
        addr = int(conn.getpeername()[1])

        logger.info(f'[SERVER] received [{addr}] : {msg} ')
        print(f'[SERVER] [{addr}] {msg}')

        # Check if current client profile was already created.
        profile_existed = any(u.addr == addr for u in self.online_users)

        if(msg.startswith('NICK ')): self.handle_NICK(conn, addr, msg, profile_existed)

        if(msg.startswith('USER ')): self.handle_USER(conn, addr, msg, profile_existed)
            
        if(msg.startswith('JOIN ')): self.handle_JOIN(conn, addr, msg, profile_existed)

        if 'PRIVMSG' in msg: self.handle_PRIVMSG(conn, msg)

        if(msg.startswith('QUIT')): return self.handle_QUIT(conn, addr, msg)


    """
    Broadcast a message server-wide.
    """
    def broadcast(self, conn, msg, to_all=False):
        for sock in self.SOCKET_LIST:
            if (sock is not self.server_socket) and ((sock is not conn) or to_all):
                print(f'[SERVER] Broadcasting: {msg}')
                sock.send(bytes(msg, common.ENCODE_FORMAT))

    """
    Close all openning sockets.
    """
    def close(self):
        for s in self.SOCKET_LIST:
            s.close()
        self.server_socket.close()

    """
    Set of functions to handle requests from client to server in RFC 1459 format
    """

    def handle_NICK(self, conn, addr, msg, profile_existed):
        nickname = msg[len('NICK '):]

        if profile_existed:
            for each_user in self.online_users:
                if each_user.addr == addr:
                    each_user.set_nickname(nickname)
                    return

        new_user = user(addr)
        new_user.set_nickname(nickname)
        self.online_users.append(new_user)

    # TODO: Extract information properly
    def handle_USER(self, conn, addr, msg, profile_existed):
        username = msg[len('USER '):]

        if profile_existed:
            for each_user in self.online_users:
                if each_user.addr == addr:
                    each_user.set_username(username)
                    return

        new_user = user(int(addr))
        new_user.set_username(username)
        self.online_users.append(new_user)

    def handle_JOIN(self, conn, addr, msg, profile_existed):
        """ Format: JOIN #global """
        channel = msg[len('JOIN '):]

        if profile_existed:
            for each_user in self.online_users:
                if each_user.addr == addr:
                    each_user.join_channel(channel)
                    if each_user.check_registered():
                        self.broadcast(conn, self.PRIVMSG('SERVER', f'Welcome {each_user.nickname} to our amazing channel\n'))
                    return

        new_user = user(addr)
        new_user.join_channel(channel)
        self.online_users.append(new_user)

    # TODO: Handle this case using regex properly.
    def handle_PRIVMSG(self, conn, msg):
        sender, _, content = common.extract_message(msg)
        prepare_msg = self.PRIVMSG(sender, content)
        self.broadcast(conn, prepare_msg, False)

    def PRIVMSG(self, sender, content):
        return f':{sender} PRIVMSG {common.CHANNEL} :{content}\n'

    def handle_QUIT(self, conn, addr, msg):
        """ Format: QUIT :reason """
        self.SOCKET_LIST.remove(conn)
        self.broadcast(conn, msg.split(':', 1)[1])

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