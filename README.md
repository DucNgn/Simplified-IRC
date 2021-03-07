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

**Note**: The `curses` package (responsible for the TUI) is not built-in on Windows Python. Run 

```
pipenv install windows-curses
```
to install `curses`.
