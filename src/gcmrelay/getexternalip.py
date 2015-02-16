'''
Prints the external IP address
Created on Feb 15, 2015

@author: Gary
'''
import socket

reflector_server_ip = '184.73.159.130'
reflector_server_port = 13374

if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((reflector_server_ip, reflector_server_port))
    s.send('getIP')
    result = s.recv(1024)
    s.close()
    print result