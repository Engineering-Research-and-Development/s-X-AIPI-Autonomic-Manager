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
