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

        logger.info(f'[SERVER] Created and binded server socket with provided address: {self.ADDR}')
        print(f'[SERVER] Created and binded server socket with provided address: {self.ADDR}')

    def start(self):
        """ Method to start the server and listen to connections incoming from clients. """
        self.server_socket.listen()
        logger.info('[SERVER] Actively listening for connection')
        print('[SERVER] Actively listening for connection')

        self.SOCKET_LIST.append(self.server_socket)

        while True:
            ready_to_read, _, _ = select.select(self.SOCKET_LIST, [], [], 0)

            for sock in ready_to_read:
                # New connection request.
                if sock is self.server_socket:
                    sockfd, addr = self.server_socket.accept()
                    self.SOCKET_LIST.append(sockfd)
                    logger.info(f'[SERVER] Received and accepted new connection from [{addr}]')
                    print(f'[SERVER] Received and accepted new connection from [{addr}]')

                # A message from client to server
                else:
                    try:
                        data = sock.recv(common.HEADER_SIZE).decode(common.ENCODE_FORMAT)
                        if data:
                            self.handle_data(sock, data)
                        else:
                            logger.debug('Broken Socket. Removing')
                            if sock in self.SOCKET_LIST:
                                self.SOCKET_LIST.remove(sock)
                                self.remove_user(int(sock.getpeername()[1]))
                    except:
                        logger.info(f'[SERVER] A client disconnected from the server')
                        print(f'[SERVER] A client disconnected from the server')
                        self.broadcast(sock, f'A client walked out of the server')
                        continue
        self.server_socket.close()

    def remove_user(self, addr):
        """ Remove a connection out of online users list """
        for each in self.online_users:
            if each.addr == addr:
                self.online_users.remove(each)


    """
    Handle the received data from a client.
    """
    def handle_data(self, conn, msg):
        addr = int(conn.getpeername()[1])

        logger.info(f'[SERVER] received [{addr}] : {msg} ')
        print(f'[SERVER] received [{addr}] : {msg}')

        # Check if current client profile was already created.
        profile_existed = any(u.addr == addr for u in self.online_users)

        if(msg.startswith('NICK ')): 
            self.handle_NICK(conn, addr, msg, profile_existed)
            return

        if(msg.startswith('USER ')): 
            self.handle_USER(conn, addr, msg, profile_existed)
            return
            
        if(msg.startswith('JOIN ')): 
            self.handle_JOIN(conn, addr, msg, profile_existed)
            return

        if(msg.startswith('QUIT')): 
            self.handle_QUIT(conn, addr, msg)
            return

        if 'PRIVMSG' in msg: 
            self.handle_PRIVMSG(conn, msg)
            return


    """
    Broadcast a message server-wide.
    """
    def broadcast(self, conn, msg, to_all=False):
        logger.debug(f'[SERVER] Broadcasting {msg}')
        print(f'[SERVER] Broadcasting {msg}')
        for sock in self.SOCKET_LIST:
            if (sock is not self.server_socket) and ((sock is not conn) or to_all):
                sock.send(bytes(msg, common.ENCODE_FORMAT))

    """
    Close all openning sockets.
    """
    def close(self):
        for s in self.SOCKET_LIST:
            s.close()
        logger.info(f'[SERVER] Successfully closed all opening sockets')
        print(f'[SERVER] Successfully closed all opening sockets')

    """
    Set of functions to handle requests from client to server in RFC 1459 format
    """

    def handle_NICK(self, conn, addr, msg, profile_existed):
        """ Format: NICK nickname """
        nickname = msg[len('NICK '):]

        duplicated = self.duplicate_NICK(addr, nickname)
        if duplicated:
            # Send error status back to client.
            conn.send(bytes(common.NICKNAMEINUSE, common.ENCODE_FORMAT))
            logger.info(f'[SERVER] [{addr}] Nick name is in use. Try another one')
            self.remove_user(addr)
            return

        if profile_existed:
            for each_user in self.online_users:
                if each_user.addr == addr:
                    each_user.set_nickname(nickname)
                    logger.info(f'[SERVER] [{addr}] Successfully set nickname')
                    return

        new_user = user(addr)
        new_user.set_nickname(nickname)
        self.online_users.append(new_user)
        logger.info(f'[SERVER] [{addr}] Successfully set nickname')

    def duplicate_NICK(self, addr, nickname):
        """ Check if a nickname existed in server """
        return any(u.nickname == nickname and u.addr is not addr for u in self.online_users)

    def handle_USER(self, conn, addr, msg, profile_existed):
        """ Format: USER username hostname servername realname """
        username = msg.split(' ')[1]

        if profile_existed:
            for each_user in self.online_users:
                if each_user.addr == addr:
                    each_user.set_username(username)
                    logger.info(f'[SERVER] [{addr}] Successfully set username')
                    return

        new_user = user(int(addr))
        new_user.set_username(username)
        self.online_users.append(new_user)
        logger.info(f'[SERVER] [{addr}] Successfully set username')

    def handle_JOIN(self, conn, addr, msg, profile_existed):
        """ Format: JOIN #global """
        channel = msg[len('JOIN '):]

        if profile_existed:
            for each_user in self.online_users:
                if each_user.addr == addr:
                    each_user.join_channel(channel)
                    logger.info(f'[SERVER] [{addr}] Successfully join the channel {channel}')
                    if each_user.check_registered():
                        self.broadcast(conn, self.PRIVMSG('SERVER', f'Welcome {each_user.nickname} to our amazing channel\n'), True)
                    return

        new_user = user(addr)
        new_user.join_channel(channel)
        self.online_users.append(new_user)
        logger.info(f'[SERVER] [{addr}] Successfully join the channel {channel}')

    def handle_PRIVMSG(self, conn, msg):
        sender, _, content = common.extract_message(msg)
        prepare_msg = self.PRIVMSG(sender, content)
        self.broadcast(conn, prepare_msg)

    def PRIVMSG(self, sender, content):
        return f':{sender} PRIVMSG {common.CHANNEL} :{content}\n'

    def handle_QUIT(self, conn, addr, msg):
        """ Format: QUIT :reason """
        self.SOCKET_LIST.remove(conn)
        self.remove_user(addr)
        logger.info(f'[SERVER] received a QUIT request from [{addr}]')
        self.broadcast(conn, str(self.find_username(addr) + ' ' + msg.split(':', 1)[1]))

    def find_username(self, addr):
        for each in self.online_users:
            if each.addr == addr:
                return each.username
    """
    End of domain
    """

def main(args):
    HOST = ''
    PORT = args.port
    try:
        server = IRCServer(HOST, PORT)
        server.start()
    except KeyboardInterrupt:
        logger.info(f'[SERVER] Keyboard interrupted server. Server is terminating')
        print(f'[SERVER] Keyboard interrupted server. Server is terminating')
        server.close()
        sys.exit()

if __name__ == '__main__':
    # create parser object
    parser = argparse.ArgumentParser(description="This is the irc client")

    # defining arguments for parser object
    parser.add_argument("-p", "--port", type=int, nargs="?",
                        metavar="PORT", default=5050,
                        help="Target port to use")

    # parse the arguments from standard input
    args = parser.parse_args()
    print(args)
    main(args)