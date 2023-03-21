import argparse
import signal
import logging
import select
import socket
from threading import Thread
import paho.mqtt.client as mqtt
from kubernetes import client, config, utils
import time
import os


FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()

LOCAL_DATA_HANDLER = lambda x:x
REMOTE_DATA_HANDLER = lambda x:x

BUFFER_SIZE = 2 ** 10

PFCP_DATA = None
PFCP_RESENDING = False

def pfcp_proxy(host, upfs):
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxy_socket.bind(ip_to_tuple(host))

    smf = None
    upf_address = ip_to_tuple(upfs)
    
    while True:
        data, address = proxy_socket.recvfrom(BUFFER_SIZE)

        if smf == None:
            smf = address

        if address == smf:
            data = LOCAL_DATA_HANDLER(data)
            PFCP_DATA = data
            print(PFCP_DATA)
            proxy_socket.sendto(data, upf_address)         
        elif address == upf_address and PFCP_RESENDING == False:
            data = REMOTE_DATA_HANDLER(data)
            proxy_socket.sendto(data, smf)
            smf = None
        elif address == upf_address and PFCP_RESENDING == True:
            PFCP_RESENDING = False
    
def resend_pfcp(upf_ip):
    proxy_socket.sendto(PFCP_DATA, upf_ip)
    PFCP_RESENDING = True

def ip_to_tuple(ip):
    ip, port = ip.split(':')
    return (ip, int(port))

def main():
    host = "10.20.1.57:8805"
    upfs = "10.20.1.58:8805"
    # pfcp_proxy(host, upfs)   
    t = Thread(target=pfcp_proxy, args=(host, upfs))
    t.start()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("try","xxxx")
    client.connect("10.0.0.218", 1883, 60)
    client.loop_forever()


def on_message(client, userdata, msg):
    print(client, userdata)
    print(msg.topic+" "+ msg.payload.decode('utf-8'))
    # if msg.payload.decode('utf-8')[msg.payload.decode('utf-8')]
    resend_pfcp(msg.payload.decode('utf-8').split(":")[1])


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("upf/status")

if __name__ == '__main__':
    main()

    

    