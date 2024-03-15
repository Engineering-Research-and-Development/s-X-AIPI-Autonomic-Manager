#!/usr/bin/env python
# coding: utf-8

import json
import requests
import subprocess
import time
import socket

from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Union, Tuple, List, Type, Any
from threading import Thread
from datetime import datetime

from utils.dag_commons import *






class ReceiverConfiguration():
    _instance = None

    def __new__(cls):
        
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Address and port of the HTTP Endpoint
        self.http_address = socket.gethostbyname(socket.gethostname())
        self.http_port = 8064
        self.request_completeness = True

            
        
class ServeThread(Thread):

    def __init__(self, request, post_data, timestamp):
        Thread.__init__(self)
        self.request = request
        self.post_data = post_data
        self.timestamp = timestamp

        
    def run(self):
        
        msg=structureNGSIRequest(self.request, self.post_data, self.timestamp)
        
        event = parse(msg)
        entity = event.entities[0]
        
        dic = {}
        dic['id'] = entity.id
        dic['type'] = entity.type
        
        for key, value in entity.attrs.items():
            dic[key] = {}
            dic[key]["type"] = value.type
            dic[key]["value"] = value.value
            

        #command = '''airflow dags trigger solution_triggerer -c ' ''' + json.dumps(dic) + ''' ' '''
        #print(command)
        #subprocess.run(command, shell=True, check=True)
        
        
        command = '''airflow dags trigger aluminium_dag -c ' ''' + json.dumps(dic) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
        return None
            
            
        
        
class NotificationRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        message = "Hello world!"
        self.wfile.write(bytes(message, "utf8"))
        return
    
    def run():
        print('Running Server...')

       
    def do_POST(self):
        '''
        Overridden POST function:
        - The server receives data from Orion or from CURL requests.
        - It structures and NGSI Request to be parsed
        - Set up a connection with the MultiThread Socket Server and sends received data
        - If succeeds, sends a confirmation message
        '''

        timestamp = datetime.now()
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        serving = ServeThread(self, post_data, timestamp)
        serving.start()

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        self.wfile.write("<html><body><h1>POST!</h1></body></html>".encode("utf-8")) 
    
    
    
    
def Start_Aluminium():

    configuration = ReceiverConfiguration()
    
    while True:
        try:
            server_address = (configuration.http_address, configuration.http_port)
            httpd = HTTPServer(server_address, NotificationRequestHandler)
            break
        except OSError as e:
            configuration.http_port += 1
        except Exception as e:
            print(e)
            exit(1)
    print(f"Bound HTTP endpoint at: {server_address}")

    httpd.serve_forever()
    threadserver = ServerThread(httpd)
    threadserver.start()
    
    return server_address



    
    
   
