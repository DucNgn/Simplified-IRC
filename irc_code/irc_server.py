"""
SERVER SIDE IMPLEMENTATION 
"""

import socket
import sys, time
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
        self.setup()

    def setup(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server.setblocking(False)
        self.server.bind(self.ADDR)

    """ 
    Method to start the server and listen to connections incoming.
    """
    def start(self):
        self.server.listen()
        logger.info(f'[SERVER] Server is listening on {self.HOST} : {self.PORT}')
        while True:
            conn, addr = self.server.accept()
            self.client_list.append(conn)
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()
            logger.info(f'[SERVER] Active connections: {len(self.client_list)}')
            logger.debug(f'[SERVER] Active threads: {threading.activeCount() - 1}')
        self.close()

    """
    Communicate with each client and decide actions.
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
    Handle the received data from client.
    Return a boolean indicates if the connection should persist.
    """
    def handle_data(self, conn, addr, msg):
        logger.info(f'[SERVER] [{addr}] {msg}')
        print(f'[SERVER] [{addr}] {msg}')

        # Denote if the client created profile before.
        connection_existed = False
        for each_user in self.online_users:
            if each_user.addr is addr:
                connection_existed = True

        if(msg.startswith('QUIT')):
            self.client_list.remove(conn)
            self.broadcast(conn, addr, msg.split(':', 1)[1])
            return False

        if(msg.startswith('NICK ')):
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

        if(msg.startswith('JOIN ')):
            channel = msg[len('JOIN '):]

            if connection_existed:
                for each_user in self.online_users:
                    if each_user.addr is addr:
                        each_user.join_channel(channel)
                        if each_user.check_registered():
                            self.broadcast(conn, addr, self.PRIVMSG('HOST', f'Welcome {each_user.nickname} to our amazing channel\n'), to_all=True)
                        return True

            new_user = user(addr)
            new_user.join_channel(channel)
            self.online_users.append(new_user)
            return True

        # TODO: Handle this case using regex properly.
        if 'PRIVMSG' in msg:
            sender, _, content = common.extract_message(msg)
            prepare_msg = self.PRIVMSG(sender, content)
            self.broadcast(conn, addr, prepare_msg, False)
            return True

        return True

    def PRIVMSG(self, sender, content):
        return f':{sender} PRIVMSG {common.CHANNEL} :{content}\n'


    """
    Broadcast a message server-wide.
    """
    def broadcast(self, conn, addr, msg, to_all=False):
        logger.info(f'[SERVER] Broadcasting message from {addr} to the whole server')
        print(f'[SERVER] Broadcasting message from {addr} to the whole server')
        print(f'[SERVER] # of sockets in list {len(self.client_list)}')
        for client_socket in self.client_list:
            if (client_socket is not conn) or to_all:
                print('Sending message: ', msg)
                try:
                    print(client_socket)
                    client_socket.send(bytes(msg, common.ENCODE_FORMAT))
                    time.sleep(1)
                except Exception as e:
                    print('Cannot send message: ', e)

    """
    Close all sockets.
    """
    def close(self):
        for s in self.client_list:
            s.close()
        self.server.close()


def main(args):
    # HOST = socket.gethostbyname(socket.gethostname())
    HOST = ''
    PORT = 5050
    try:
        server = IRCServer(HOST, PORT)
        server.start()
    except KeyboardInterrupt:
        logger.info(f'[SERVER] Keyboard interrupted server. Server is terminating')
        server.close()
        sys.exit()

if __name__ == '__main__':
    # TODO: Pass arguments properly here
    args = None
    main(args)