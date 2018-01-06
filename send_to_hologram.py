#!/usr/bin/env python2.7

import sys
from Hologram.HologramCloud import HologramCloud

credentials = {'devicekey': ''}
hologram = HologramCloud(credentials, network='cellular')

def send_messages(messages):
    if len(messages) < 1:
        return

    result = hologram.network.connect()
    if result == False:
        print ' Failed to connect to cell network'

    for message in messages:
        response_code = hologram.sendMessage(message)
        # Prints 'Message sent successfully: xxxxxx'.
        print('{} : {}'.format(hologram.getResultString(response_code), message)) 

    hologram.network.disconnect()

def main(argv):
    if (len(argv) < 1):
        print("No messages to send")
        return
    else:
        print("Messages to send: {}".format(str(argv)))
        send_messages(argv)

if __name__ == "__main__":
    main(sys.argv[1:])