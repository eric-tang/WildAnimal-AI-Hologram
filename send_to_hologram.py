#!/usr/bin/env python2.7

import argparse
from Hologram.HologramCloud import HologramCloud
from Hologram.CustomCloud import CustomCloud

credentials = {'devicekey': ''}
hologram_cloud = HologramCloud(credentials, network='cellular')
custom_cloud = CustomCloud(dict(), send_host='192.168.1.14', send_port=9999)

def send_messages(messages, is_custom_cloud=False):
    if len(messages) < 1:
        return

    
    if is_custom_cloud:
        cloud_obj = custom_cloud
    else:
        cloud_obj = hologram_cloud
        result = cloud_obj.network.connect()
        if result == False:
            print ' Failed to connect to cell network'
            return

    for message in messages:
        response = cloud_obj.sendMessage(message)
        # Prints 'Message sent successfully: xxxxxx'.
        if is_custom_cloud:
            result_string = 'Message sent successfully'
        else:
            result_string = cloud_obj.getResultString(response)
        print('{} : {}'.format(result_string, message)) 

    if not is_custom_cloud:
        cloud_obj.network.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send messages to HologramCloud or CustomCloud through Hologram Nova')
    parser.add_argument('messages', nargs='+', help='the messages to be sent out')
    parser.add_argument('--custom-cloud', action='store_true', \
                    help='send to custom cloud (default: send to HologramCloud)')

    args = parser.parse_args()
    send_messages(args.messages, args.custom_cloud)