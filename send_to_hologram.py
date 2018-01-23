#!/usr/bin/env python2.7

import argparse
import os
from Hologram.HologramCloud import HologramCloud
from Hologram.CustomCloud import CustomCloud

credentials = {'devicekey': ''}
hologram_cloud = HologramCloud(credentials, network='cellular')
custom_cloud = CustomCloud(dict(), send_host='localhost', send_port=9999, network='cellular')

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
        m = message + "\n"
        response = cloud_obj.sendMessage(m)

        if is_custom_cloud:
            result_string = 'Message sent successfully'
        else:
            result_string = cloud_obj.getResultString(response)
        print(result_string) 
    
    cloud_obj.network.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send messages to HologramCloud or CustomCloud through Hologram Nova')
    parser.add_argument('-m', '--messages', nargs='+', help='the messages to be sent out')
    parser.add_argument('-d', '--input-dir', help='A folder path including files of contents to be sent out')
    parser.add_argument('--custom-cloud', action='store_true', \
                    help='send to custom cloud (default: send to HologramCloud)')

    args = parser.parse_args()
    if args.input_dir is not None:
        for file_name in os.listdir(args.input_dir):
            file_path = os.path.join(args.input_dir, file_name)
            with open(file_path, 'r') as input_file:
                message_to_send = input_file.read()
                print('Sending data from file {}'.format(file_path))
                send_messages([message_to_send], args.custom_cloud)
    else:
        send_messages(args.messages, args.custom_cloud)