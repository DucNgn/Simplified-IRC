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
