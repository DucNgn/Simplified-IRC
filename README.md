# Simplified IRC

## About
Main purpose of this repo is to implement a simple client & server in Python with socket programming.

+ [Handout](./A2_socket_programming.pdf)

## Requirements:

+ Python 3.8
+ [pipenv](https://github.com/pypa/pipenv) for virtual environment.

## Set up
+ `pipenv shell` to start the virtual shell.
+ `pipenv install` to install dependencies.
+ `pipenv install --dev` to install dev dependencies.

**Note**: The `curses` and `argparse` packages (responsible for the TUI) is not built-in on Windows Python. Run 

```
pipenv install -r requirements.txt
```

to install `curses` and `argparse`.

+ Full list of requirements is in `requirements.txt`

## Run
+ `python irc_server.py` inside `irc_code` folder to start up the server.
+ `python irc_client.py` inside `irc_code` folder to start a client (can start many). Command `/quit` to quit from client side.

## Explanation:
### Structure:
+ `common.py` includes the common methods and constant accross the app.
+ `irc_server.py` is the server of the IRC.
+ `irc_client.py` is the client of the IRC.

### Design:

#### Server
+ The server starts by binding host and port according to the provided configurations (command line arguments) in nonblocking mode. Then it uses `select()` to manage readable sockets. Upon a socket found in `ready_to_read` list, the server handles by calling `handle_data()` to process the received message or establish a new socket (for the new connection request if `server_socket` is found in `ready_to_read`).
+ In `handle_data()`, the server processes the received message according to RFC protocol.
+ `broadcast()` is used to send message from server to all of its clients via socket (exclude the sender and the `server_socket`).

+ Information for [non-blocking-sockets](https://docs.python.org/3/howto/sockets.html#non-blocking-sockets)

#### Client
+ The client receives arguments (server, port, nickname, username) from the command line.
and establish a connection to the server. It then proceed to register an user profile with the server using NICK and USER commands of RFC protocol. If the nickname already existed in the server, the client will receive a status of `ERR_NICKNAMEINUSE` and terminates.
+ The client then joins a channel (default `#global`).
+ After registering with the server successfully, the client can send message to the server using `PRIVMSG` command. The server will extract the message and broadcast server-wide to other connected clients at the moment.
+ For receiving messages, client creates a new thread to continuously listen for any data coming back from the server and put it up for display in the TUI.
+ When client wants to quit, type `\quit` in the chat will issue a QUIT command to the server. The server handles the command by closing the socket and delete the user profile. Client also closes its socket before terminating.
