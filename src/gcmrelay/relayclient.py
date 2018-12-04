'''
The purpose of the gcmrelay package is to provide a mechanism for sending GCM message
to Google from a known IP address when the actual message may original from a machine
with changing IP addresses (e.g. something within a home network).

relayclient is the client app which is invoked to send message to the relay server which 
will then call the GCM server

Created on Sep 8, 2014

@author: Gary O'Neall
'''
import socket
import json
import constants
from pyotp.hotp import HOTP

def recieveJson(skt):
    skt.settimeout(3.0)
    json = ''
    try:
        ch = skt.recv(1)
        if ch != '{':
            raise Exception("Invalid JSON response - missing '{'")
        braceCount = 1
        json += ch
        while braceCount > 0 and len(json) < constants.MAX_MSG_SIZE:
            ch = skt.recv(1)
            if ch == '{':
                braceCount = braceCount + 1
            elif ch == '}':
                braceCount = braceCount - 1
            json += ch
        if len(json) >= constants.MAX_MSG_SIZE:
            raise Exception("Invalid JSON response -exceeds maximum size")
    except socket.timeout:
        return json 
    return json

class GcmRelayClient:
    
    hotp = HOTP(constants.verification)
    request_num = 0
    
    def __init__(self, ip_address, port, api_key):
        self.ip_address = ip_address
        self.port = port
        self.api_key = api_key
 
    '''
    Send a message to the relay server which will then forward the message on to the GCM server
    '''       
    def send(self, registration_ids, data):
        auth = self.hotp.at(self.request_num)
        payload = {constants.key_api_key : self.api_key, 
                   constants.key_request : constants.request_forward_gcm_message,
                   constants.key_registration_ids : registration_ids,
                   constants.key_request_number : self.request_num,
                   constants.key_authentication : auth}
        self.request_num = self.request_num + 1
        if data:
            payload[constants.key_data] =  data
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.ip_address, self.port))
            s.sendall(json.dumps(payload))
            result = json.loads(recieveJson(s))          
        except Exception as e:
            result = {constants.key_error : 'Exception from client send: ' + e.message}
        finally:
            if s:
                s.close()
        return result
