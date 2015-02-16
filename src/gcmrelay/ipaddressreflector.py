'''
Socket server which simply reflects the IP address of the caller
Created on Feb 15, 2015

@author: Gary O'Neall
'''

import sys
import logging
import SocketServer
import json
import constants
import gcmclient.gcm
from pyotp.hotp import HOTP

server_ip_address = '10.0.0.7'
server_port = 13374

class IpReflectorServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

class IpReflectorHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        client_ip = str(self.client_address[0])
        self.request.sendall(client_ip)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        server_ip_address = sys.argv[1]
    if len(sys.argv) > 2:
        server_port = sys.argv[2]
    server = IpReflectorServer((server_ip_address, server_port), IpReflectorHandler)
    server.serve_forever()