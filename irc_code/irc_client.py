#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021
#
# Distributed under terms of the MIT license.

"""
Description:

"""
import socket
import asyncio
import sys, time
import threading
import argparse

import patterns
import logging
import view
import common

logging.basicConfig(filename='view.log', level=logging.DEBUG)
logger = logging.getLogger()

class IRCClient(patterns.Subscriber):
    registered = False
    client = socket.socket()
    stop_event = False

    def __init__(self, HOST, PORT, username, nickname):
        super().__init__()
        self.username = username
        self.nickname = nickname
        self._run = True
        self.HOST, self.PORT = HOST, PORT
        self.ADDR = (HOST, PORT)
        self.setup_client()

    """
    Connect, register, join channel.
    """
    def setup_client(self):
        self.connect()
        self.register()
        self.join()
        logger.info(f'[IRCClient] Successfully setup user account')

    """
    Connect to the server.
    """
    def connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(self.ADDR)
            logger.debug(f'[IRCClient] Successfully connected to the server')
        except ConnectionRefusedError as e:
            logger.debug(f'[IRC CLIENT] [{self.username}] failed to connect to the server. {e}')
            sys.exit()

    """
    Register client using provided username and nickname
    """
    def register(self):
        self.client.send(bytes(self.NICK(), common.ENCODE_FORMAT))
        time.sleep(1)
        self.client.send(bytes(self.USER(), common.ENCODE_FORMAT))
        time.sleep(1)
        logger.debug(f'[IRCClient] Successfully registered client with the server')
        self.registered = True

    """
    Automatically join #global.
    """
    def join(self):
        self.client.send(bytes(self.JOIN(common.CHANNEL), common.ENCODE_FORMAT))
        time.sleep(1)
        logger.debug(f'[IRCClient] Successfully joined channel {common.CHANNEL}')

    def set_view(self, view):
        self.view = view

    def update(self, msg):
        # Will need to modify this
        if not isinstance(msg, str):
            raise TypeError(f"Update argument needs to be a string")
        elif not len(msg):
            # Empty string
            return
        logger.info(f"IRCClient.update -> msg: {msg}")
        self.process_input(msg)

    def process_input(self, msg):
        self.add_msg(msg)
        if msg.lower().startswith('/quit'):
            self.close(' left the chat')
            raise KeyboardInterrupt
        else:
            self.send_message(msg)

    """
    Send message to channel.
    """
    def send_message(self, msg):
        send_msg = self.PRIVMSG(msg)
        logger.debug(f'Sending message {send_msg} to server')
        self.client.send(bytes(send_msg, common.ENCODE_FORMAT))
        time.sleep(1)

    """
    Add message to view.
    """
    def add_msg(self, msg):
        self.view.add_msg(self.nickname, msg)

    """
    Add message to view from outsider.
    """
    def add_msg_outside(self, nickname, msg):
        self.view.add_msg(nickname, msg)

    def run(self):
        while True:
            if self.stop_event:
                break
            msg_received = self.client.recv(common.HEADER_SIZE).decode(common.ENCODE_FORMAT)
            time.sleep(1)
            logger.debug(f'[IRC Client] Received message from Server: {msg_received}')
            self.handle_data(msg_received)

    def stop_thread(self):
        logger.debug('[IRCClient] Sending stop event to Thread')
        self.stop_event = True

    """
    Handle data received from server.
    """
    def handle_data(self, msg):
        # Message comes in the form of :sender PRIVMSG nick :content
        # TODO: use regex to detect PRIVMSG
        if 'PRIVMSG' in msg:
            sender, _, content = common.extract_message(msg)
            self.add_msg_outside(sender, content)
            return

        if msg == common.NICKNAMEINUSE:
            self.add_msg_outside('SERVER','Nick name is already in use. Please try again')
            self.close('Nick name is in used')
            sys.exit()

    """
    Close sockets with reason.
    """    
    def close(self, reason):
        self.stop_thread()
        logger.debug(f"[IRCClient] Closing socket because {reason}")
        self.client.send(bytes(f'{self.QUIT(reason)}', common.ENCODE_FORMAT))
        self.client.close()
        sys.exit()

    """
    Set of functions to compose the correct syntax of RFC protocol.
    """ 
    def QUIT(self, reason):
        return f'QUIT :{reason}'

    def NICK(self):
        return f'NICK {self.nickname}'

    def USER(self):
        return f'USER {self.username} {self.HOST} {self.HOST} :{self.username}' 

    def JOIN(self, channel):
        return f'JOIN {channel}'

    def PRIVMSG(self, msg):
        return f':{self.nickname} PRIVMSG {common.CHANNEL} :{msg}\n'


def main(args):
    # TODO: command line argument to do this properly.
    # HOST = socket.gethostbyname(socket.gethostname())
    HOST = args.server
    PORT = args.port
    username = args.username
    nickname = args.nickname

    # Start a thread to wait for messages coming back from host
    client = IRCClient(HOST, PORT, username, nickname)
    thread = threading.Thread(target=client.run)
    thread.start()
    logger.debug(f'[IRCClient] Client thread started')

    logger.info(f"Client object created")
    with view.View() as v:
        logger.info(f"Entered the context of a View object")
        client.set_view(v)
        logger.debug(f"Passed View object to IRC Client")
        v.add_subscriber(client)
        logger.debug(f"IRC Client is subscribed to the View (to receive user input)")
        async def inner_run():
            await asyncio.gather(
                v.run(),
                return_exceptions=True,
            )
        try:
            asyncio.run( inner_run() )
        except KeyboardInterrupt:
            logger.debug(f"Signifies end of process")
    client.close('IRC Client object terminated')

if __name__ == "__main__":
    # create parser object
    parser = argparse.ArgumentParser(description="This is the irc client")

    # defining arguments for parser object
    parser.add_argument("-s", "--server", type=str, nargs="?",
                        metavar="SERVER", default="localhost",
                        help="Target server to initiate a connection to")

    parser.add_argument("-p", "--port", type=str, nargs="?",
                        metavar="PORT", default=5050,
                        help="Target port to use")

    parser.add_argument("-n", "--nickname", type=str, nargs="?",
                        metavar="NICKNAME", default="GuestNick",
                        help="Target nickname to use")

    parser.add_argument("-u", "--username", type=str, nargs="?",
                        metavar="USERNAME", default="GuestUser",
                        help="Target username to use")

    # parse the arguments from standard input
    args = parser.parse_args()
    logger.info(f'[IRCClient] Received arguments from command line: {args}')
    main(args)
