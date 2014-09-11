'''
The purpose of the gcmrelay package is to provide a mechanism for sending GCM message
to Google from a known IP address when the actual message may original from a machine
with changing IP addresses (e.g. something within a home network).

relayserver is a relay server module for a TCP server which runs on a machine with a known IP address
The relay server essentially listens to an IP address for connections from the relay
client then forwards on the JSON request to GCM.

If this module is run from the command line, it will startup and run the server until it is killed with
two optional parameters:
  server_ip_address
  server_port

Created on Sep 8, 2014
@author: Gary O'Neall
'''

import sys
import logging
import SocketServer
import json
import constants
import gcmclient.gcm
from pyotp.hotp import HOTP

log_file_name = 'gcmrelayserver.log'
logging.basicConfig(filename=log_file_name,level=logging.INFO)
server_ip_address = '10.0.0.7'
server_port = 13373
hotp = HOTP(constants.verification)

class GcmRelayServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

class GcmRelayHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            gcmpayload = json.loads(self.request.recv(constants.MAX_MSG_SIZE).strip())
            # parse out the data
            request_num = gcmpayload[constants.key_request_number]
            auth = gcmpayload[constants.key_authentication]
            reg_ids = gcmpayload[constants.key_registration_ids]
            gcm_data = gcmpayload[constants.key_data]
            api_key = gcmpayload[constants.key_api_key]
            saServerGcm = gcmclient.gcm.GCM(api_key)
            if (hotp.verify(auth, request_num)):
                response = saServerGcm.json_request(registration_ids=reg_ids, data=gcm_data)
                logging.info('Sent message number '+ str(request_num) + ' to GCM')
            else:
                logging.error('Authentication failed from IP address '+str(self.client_address[0]))
                response = {constants.key_error, 'Authentication Failed'}
            self.request.sendall(json.dumps(response))
        except Exception, e:
            logging.error('Exception during gcm_send: ' + e.message)
            response = {constants.key_error : 'Exception from gcm_send: ' + e.message}
            self.request.sendall(json.dumps(response))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        server_ip_address = sys.argv[1]
    if len(sys.argv) > 2:
        server_port = sys.argv[2]
    server = GcmRelayServer((server_ip_address, server_port), GcmRelayHandler)
    server.serve_forever()