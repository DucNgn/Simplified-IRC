"""
Set of helper functions.
"""

ENCODE_FORMAT = 'utf-8'
HEADER_SIZE = 2048
CHANNEL = '#global'
NICKNAMEINUSE = 'ERR_NICKNAMEINUSE'

def extract_message(msg):
    # Handle message in the form of `:sender PRIVMSG receiver :content`
    header = msg.split(':')[1]
    (sender, receiver) = extract_header(header)
    content = msg.split(':')[2]
    return (sender, receiver, content)


def extract_header(header):
    sender = header.split(' ')[0]
    receiver = header.split(' ')[2]
    return (sender, receiver)