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

import patterns
import logging
import view
import common

logging.basicConfig(filename='view.log', level=logging.DEBUG)
logger = logging.getLogger()

class IRCClient(patterns.Subscriber):
    connected = False
    registered = False
    client = socket.socket()

    def __init__(self, HOST, PORT, username, nickname):
        super().__init__()
        self.username = username
        self.nickname = nickname
        self._run = True
        self.HOST, self.PORT = HOST, PORT
        self.ADDR = (HOST, PORT)
        self.setup_client()

    def setup_client(self):
        self.connect()
        while not self.registered:
            self.register()
        self.join()

    # Connect to server
    def connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(self.ADDR)
            self.connected = True
        except ConnectionRefusedError as e:
            logger.debug(f'[IRC CLIENT] [{self.username}] failed to connect to the server. {e}')
            sys.exit()

    """
    Register client using username and nickname
    """
    def register(self):
        self.client.send(bytes(self.NICK(), common.ENCODE_FORMAT))
        time.sleep(1)
        self.client.send(bytes(self.USER(), common.ENCODE_FORMAT))
        time.sleep(1)
        logger.debug(f'[IRCClient] Successfully registered client')
        self.registered = True

    def join(self):
        self.client.send(bytes(self.JOIN(common.CHANNEL), common.ENCODE_FORMAT))
        time.sleep(1)
        logger.debug(f'[IRCClient] Successfully join channel {common.CHANNEL}')

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
        self.send_message(msg)
        if msg.lower().startswith('/quit'):
            # Command that leads to the closure of the process
            raise KeyboardInterrupt

    def send_message(self, msg):
        self.client.send(bytes(self.PRIVMSG(msg), common.ENCODE_FORMAT))
        time.sleep(1)

    def add_msg(self, msg):
        self.view.add_msg(self.username, msg)

    def add_msg_outside(self, username, msg):
        self.view.add_msg(username, msg)

    async def run(self):
        """
        Driver of your IRC Client
        """
        while True:
            msg_received = self.client.recv(common.HEADER_SIZE).decode(common.ENCODE_FORMAT)
            time.sleep(1)
            # print('Received back: ', msg_received)
            self.handle_data(msg_received)

    def handle_data(self, msg):
        # Message comes in the form of :sender PRIVMSG nick :content
        # TODO: use regex to detect PRIVMSG
        if 'PRIVMSG' in msg:
            sender, _, content = common.extract_message(msg)
            self.add_msg_outside(sender, content)
            return
        

    def extract_header(self, header):
        sender = header.split(' ')[0]
        receiver = header.split(' ')[2]
        return (sender, receiver)

    # Close IRC client object
    def close(self):
        # Terminate connection
        logger.debug(f"Closing IRC Client object")
        if (self.connected):
            reason = 'IRC client object terminated'
            msg = f'{self.QUIT(reason)}'
            self.client.send(bytes(msg, common.ENCODE_FORMAT))
    
    # Message to signal server to terminate connection.
    def QUIT(self, reason):
        return 'QUIT' + ' :' + reason

    def NICK(self):
        return f'NICK {self.nickname}'

    def USER(self):
        return f'USER {self.username} {self.HOST} {self.HOST} :{self.username}' 

    def JOIN(self, channel):
        return f'JOIN {channel}'

    def PRIVMSG(self, msg):
        return f':{self.username} PRIVMSG {common.CHANNEL} :{msg}\n'


def main(args):
    # TODO: command line argument to do this properly.
    # HOST = socket.gethostbyname(socket.gethostname())
    HOST = 'localhost'
    PORT = 5050
    username = 'Duke'
    nickname = 'Batman'

    client = IRCClient(HOST, PORT, username, nickname)

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
                client.run(),
                return_exceptions=True,
            )
        try:
            asyncio.run( inner_run() )
        except KeyboardInterrupt:
            logger.debug(f"Signifies end of process")
    client.close()

if __name__ == "__main__":
    # Parse your command line arguments here
    args = None
    main(args)
