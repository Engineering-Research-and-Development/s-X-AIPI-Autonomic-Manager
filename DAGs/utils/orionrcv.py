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


class NGSIAttribute():
    
    def __init__(self, attrype, value, metadata):
        self.type = attrype
        self.value = value
        self.metadata = metadata
        

class NGSIEntityv2():
    
    def __init__(self, entityid, nodetype, attributes):
        self.id = entityid
        self.type = nodetype
        self.attrs = attributes



class NGSIEntityLD():
    
    def __init__(self, entityid, nodetype, attributes, context):
        self.context = context
        self.id = entityid
        self.type = nodetype
        self.attrs = attributes
        
        
class NGSIEventLD():
    
    def __init__(self, timestamp, svc, svcpath, entities):
        self.creationtime = timestamp
        self.service = svc
        self.servicePath = svcpath
        self.entities = entities
        

class NGSIEventv2():
    
    def __init__(self, timestamp, svc, svcpath, entities):
        self.creationtime = timestamp
        self.service = svc
        self.servicePath = svcpath
        self.entities = entities



class ReceiverConfiguration():
    _instance = None

    def __new__(cls):
        
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Address and port of the HTTP Endpoint
        self.http_address = socket.gethostbyname(socket.gethostname())
        self.http_port = 8061
        self.request_completeness = True




def parse_context(api_json: dict) -> Tuple[str, bool]:
    '''
    This function checks if payload is "NGSI-LD" and returns its context,
    otherwise returns False.
    Context is checkable in both "Link" Header, otherwise in JSON body
    '''
    context = api_json.get("Link", "")
    if context:
        return context, True
    else:
        context = api_json.get("Body", {}).get("@context", "")
        if context:
            return context, True
        else:
            return "", False

        
        
def parse_entities(api_json: dict) -> List[Union[NGSIEntityv2, NGSIEntityLD]]:
    '''
    A function to parse Entity in format of NGSI v2 or LD
    based on the JSON body
    '''

    #Checking all entities in JSON
    entities_data = api_json.get("Body", {}).get("data", [])
    entities = []
    for ent in entities_data:
        ent_id = ent.get("id")
        ent_type = ent.get("type")
        attributes = {}

        # Checking for all attributes in entity except for id and type
        for key in ent.keys():
            if key not in ["id", "type"]:
                if ent[key]['type'] == "Relationship":
                    attribute = NGSIAttribute(ent[key]['type'], ent[key]['object'],
                                              ent[key].get("metadata", {}))
                else:
                    attribute = NGSIAttribute(ent[key]['type'], ent[key]['value'],
                                              ent[key].get("metadata", {}))
                attributes[key] = attribute

        # Checking for Linked Data Flag
        context, is_ld = parse_context(api_json)
        if is_ld:
            entity = NGSIEntityLD(ent_id, ent_type, attributes, context)
        else:
            entity = NGSIEntityv2(ent_id, ent_type, attributes)
        entities.append(entity)
    return entities


    
def parse(structured_NGSI_request : str) -> Union[NGSIEventv2, NGSIEventLD]:
    '''
    A function to convert API response into NGSIEvents
    '''
    
    api_json = json.loads(structured_NGSI_request)
    timestamp = api_json.get("timestamp", "")
    service = api_json.get("Fiware-Service", "")
    service_path = api_json.get('Fiware-Servicepath', "")
    entities = parse_entities(api_json)
    _, is_ld = parse_context(api_json)

            
    if is_ld:
        return NGSIEventLD(timestamp, service, service_path, entities)
    else:
        return NGSIEventv2(timestamp, service, service_path, entities)




def structureNGSIRequest(request: str, body: str, timestamp: str) -> str:
    '''
    This function checks from the configuration file if the incoming message should be interpreted
    as a regular Context Broker Subscription (containing both headers and body) or if the message
    is sent via CURLS (body only).
    Based on the result, it starts to build the correct message, decoding it from the HTTP Response.
    '''
    # Loading Configuration file for request completeness

    body = body.decode('utf-8')
    print(body)


    message = "{"
        
    for line in body.split(","):
        if "notifiedAt" in line:
            timestamp_line = line
            iso_timestamp = timestamp_line.split('"')[3]
        else:
            iso_timestamp = timestamp.isoformat()   
    message = message + '"{}":"{}",'.format("timestamp", iso_timestamp)
    
    for field in request.headers:
        message = message + '"{}":"{}",'.format(field,request.headers[field].replace('"', "'"))

    # Building body of message
    message = message + '"Body":{}'.format(body)
    message = message + "}\n"

    return message
    
    
    
    
    
class ServerThread(Thread):
    
    def __init__(self, server):
        Thread.__init__(self)
        self.server = server
        
    def run(self):
        self.server.serve_forever()
        
            
        
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
            
        
        
        
        command = '''airflow dags trigger solution_triggerer -c ' ''' + json.dumps(dic) + ''' ' '''
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
    
    
    
    
def Start():

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



    
    
   
