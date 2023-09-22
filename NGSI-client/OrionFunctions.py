#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json


# In[ ]:


BASE_URL_V2 = "http://136.243.156.113:1026/v2/"
BASE_URL = "http://136.243.156.113:1026/ngsi-ld/v1/"


# In[ ]:


FIWARE_SERVICE = ""
FIWARE_SERVICEPATH = "/"


# In[ ]:


# example of an attribute body. Insert multiple bodies in a list to have an attribute list
ATTR_MODIFIED_BODY = '''
"Attr_name" : { 
    "value" : val,
    "type" : Type,
    "metadata" : {}
}
'''


# In[ ]:


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


# In[ ]:


def SelectAttributes(entity, mode='MONITOR'):

        
    attrlist = [attr for attr in entity.attrs]
        
    if mode == 'MONITOR':    
        print("Type the attribute number you want to CHANGE. Type '>QUIT' to stop. Type '>ALL' to insert all attributes")
    elif mode == 'CONDITION':
        print("Type the attribute number you want to set as CONDITION. Type '>QUIT' to stop. Type '>ALL' or '>QUIT' if no attribute is selected to insert all attributes")
    continuing = True
    returnlist = []
    while continuing:
        showlist = [str(idx+1)+"):"+attr for idx, attr in enumerate(attrlist)]
        print(showlist)
        try:
            if len(attrlist) <= 0:
                continuing = False
                print("Attribute list is now empty, quitting selection...")
                continue
            string = str(input("Insert attribute name: "))
                
                    
            if string.upper() == '>QUIT':
                print("Quitting Selection")
                continuing = False
                
                
            elif string.upper() == '>ALL':
                print("Inserting All attributes")
                continuing = False
                if mode == 'MONITOR':
                    returnlist = attrlist
                elif mode == 'CONDITION':
                    returnlist = []
                    
                    
            elif int(string) > 0 and int(string) <= len(attrlist):
                index = int(string) -1
                print("Attribute {} found. Adding to attributes".format(attrlist[index]))
                returnlist.append(attrlist[index])
                attrlist.remove(attrlist[index])
              
            else:
                print("Attribute not found, please, type it correctly. The remaining list of attributes is:", showlist)
        except Exception as e:
            print(e)
            #return
                
    return returnlist


# In[ ]:


def ReturnEntityIfExists(ent):

    isLD = False
    keys = list(ent)
    attrs = {}
        
    ID = ent['id']
    keys.remove('id')
    typ = ent['type']
    keys.remove('type')
        
    if '@context' in keys:
        context = ent['@context']
        isLD = True
        keys.remove('@context')
        
    for i in range (0, len(keys)):
        att = ent[keys[i]]
        atttype = att['type']
            
        if atttype == "Relationship":
            attval = att['object']
        else:
            attval = att['value']
            
            
        try:
            attmeta = att['metadata']
        except:
            attmeta = {}
            
        attribute = NGSIAttribute(atttype, attval, attmeta)
        attrs[keys[i]] = attribute
       
    if isLD:
        entity = NGSIEntityLD(ID, typ, attrs, context)
    else:
        entity = NGSIEntityv2(ID, typ, attrs)
        
    
    return entity, isLD


# In[ ]:


def ClearForbiddenChars(string):

    string = string.replace("<", "")
    string = string.replace(">", "")
    string = string.replace("'", "")
    string = string.replace('"', "")
    string = string.replace("=", "")
    string = string.replace(";", "")
    string = string.replace("(", "")
    string = string.replace(")", "")

    return string


# In[ ]:


def InsertTextField(phrase):

    while True:
        try: 
            text = input(phrase)
            return text
        except Exception as e:
            print("Something went wrong while inserting the new field: ", e)
            continue


# In[ ]:


def AddAttrType():

    types = {'1' : "Property",
             '2' : "Relationship",
             '3' : "GeoProperty"}
    
    while True:
        try: 
            att_type = input('''Please, select the attribute, typing a number, among:\n
                        1: Property\n
                        2: Relationship\n
                        3: GeoProperty\n''')

            value = types[att_type]
            return value
            
        except Exception as e:
            print("Something went wrong while setting attribute type: ", e)
            continue


# In[ ]:


def AddAttrValue():
    
    while True:
        try: 
            att_value = input("Please, type the attribute value. It will be inputed as text:\n")
            return att_value
        except Exception as e:
            print("Something went wrong while setting attribute value: ", e)
            continue


# In[ ]:


def RUSure(attr):

    print(f"name: {attr[0]}, type: {attr[1]}, {attr[2]}: {attr[3]}")
    while True:
        try: 
            resp = input("Are you sure? y/n")
            if resp == "y":
                return True
            elif resp == "n":
                return False
            else:
                raise Exception("Please, insert y or n \n")
        except Exception as e:
            print("Something went wrong: ", e)
            continue


# In[ ]:


def AddNewAttr():

    while True:
        try: 
            name = InsertTextField("Please, type the attribute name:\n")
            type = AddAttrType()
            value = InsertTextField("Please, type the attribute value. It will be parsed as text:\n")

            val_field = "value"
            
            if type == "Relationship":
                val_field = "object"
                
            attr = [name, type, val_field, value]
            resp = RUSure(attr)
            if resp:
                return attr
            else:
                return None
        except Exception as e:
            print("Something went while adding the new attribute: ", e)
            continue
        


# In[ ]:


def AddAttributes():

    list = []
    
    while True:
        try:
            resp = input("Do you want to add an attribute? Type y/n:\n")
            if resp == "y":
                attr = AddNewAttr()
                if attr:
                    list.append(attr)
            elif resp == "n":
                return list
        except Exception as e:
            print("Something went wrong while adding the attributes: ", e)
            continue


# In[ ]:


def ModifyAttributes(id):

    list = []
    
    while True:
        try:
            resp = input("Do you want to add an attribute? Type y/n:\n")
            if resp == "y":
                attr = AddNewAttr()
                if attr:
                    list.append(attr)
            elif resp == "n":
                return list
        except Exception as e:
            print("Something went wrong when modifying the attribute: ", e)
            continue


# In[ ]:


def BuilEntityJSON(id, type, attrs, context):

    ent = {}
    ent['@context'] = context
    ent['id'] = ClearForbiddenChars(id)
    ent['type'] = type
    
    for attr in attrs:
        key1 = ClearForbiddenChars(attr[0])
        key2 = attr[2]
        ent[key1] = {}
        ent[key1]['type'] = ClearForbiddenChars(attr[1])
        ent[key1][key2] = ClearForbiddenChars(attr[3])

    return json.dumps(ent)


# In[ ]:


def GetNGSIEntity(url, id):

    ent = GetEntityByID(url, id)
    ent, _ = ReturnEntityIfExists(ent)
    return ent


# In[ ]:


def GenerateUpdatedBody(ent, attrs):

    if len(attrs) == 1:
        attrs = list(attrs)
    elif len(attrs) < 1:
        return

    body = {}
    for attr in attrs:
        body[attr] = ent[attr]

        
    


# In[ ]:


def GuideUpdate(ent, attrs):

    if len(attrs) == 1:
        attrs = list(attrs)
    elif len(attrs) < 1:
        return

    body = {}
    for attr in attrs:
        val = ent[attr]
        val_type = "value" 
        if ent[attr]["type"] == "Relationship":
            val_type = "object"
        
        new_value = InsertTextField(f"Current Value is {ent[attr][val_type]}. Type new value:\n")
        ent[attr][val_type] = ClearForbiddenChars(new_value)
        body[attr] = ent[attr]

    return json.dumps(body)
        
    


# In[ ]:


############################ USABLE_APIs


# In[ ]:





# In[ ]:


def GetAllEntitiesV2(url):
    # Get list of entities in NGSIv2 format
    # Use only to check for available IDs

    response = requests.get(url+"entities/")
    print(response.status_code)
    js = response.json()

    for entity in js:
        print(entity['id'])


# In[ ]:


def GetEntityByID(url, id):
    # Get an entity in NGSI-LD format

    response = requests.get(url+f"entities/{id}")
    print(response.status_code)
    jresp = response.json()
    print(jresp)

    return jresp


# In[ ]:


def DeleteEntityByID(url, id):
    # Delete an entity by providing its ID

    response = requests.delete(url+f"entities/{id}")
    print(response.status_code)
    print(response.text)


# In[ ]:


def CreateEntity(url, entity_id=None, entity_type=None, attr_list=None, context=None):
    # Create an entity providing its ID, its type and a list of attributes
    # Attributes should contain at least a type field and the value field
    # The code guides you inserting values if some data is missing, but does not double check typing
    
    try:
        if entity_id is None or entity_type is None or attr_list is None:
            entity_id = InsertTextField("Please, insert the ID of the entity:\n")
            if "urn:" not in entity_id:
                entity_id = "urn:ngsi-ld:"+entity_id
            entity_type = InsertTextField("Please, insert the entity type:\n")
            attr_list = AddAttributes()
            context = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
    
        body = BuilEntityJSON(entity_id, entity_type, attr_list, context)
    
        headers = headers= {"Content-Type": "application/ld+json",                             "Fiware-Service": FIWARE_SERVICE,                             "Fiware-ServicePath": FIWARE_SERVICEPATH                            }
    
        url = url+"entities/"
    
        response = requests.post(url, body, headers=headers)
        print(response.status_code) 
        print(response.text)
        return
    except Exception as e:
        print("Something went wrong trying the creation of the entity", e)
    
    


# In[ ]:


def ModifyEntity(url, id, attr_modified = None):
    # Gets an entity by its ID and provide the list of attributes
    # Guides you updating some attributes

    ent = GetEntityByID(url, id)
    ent_id = ent['id']
    body = {}

    if attr_modified is not None:
        for key in attr_modified:
            try:
                field = ent[key]['type']
                if field == "Relationship":
                    new_val = attr_modified[key]['object']
                    ent[key]['object'] = new_val
                elif field == "Property":
                    new_val = attr_modified[key]['value']
                    ent[key]['value'] = new_val

            except Exception as e:
                print("Something went wrong while overwriting attributes:", e)
                break
        body = GenerateUpdatedBody(ent, attr_modified)
            
    else:
        ngsient, _ = ReturnEntityIfExists(ent)
        attrlist = SelectAttributes(ngsient)
        body = GuideUpdate(ent, attrlist)

    print(body)
    headers = headers= {"Content-Type": "application/json",                             "Fiware-Service": FIWARE_SERVICE,                             "Fiware-ServicePath": FIWARE_SERVICEPATH                        }
    
    url = url+f'entities/{ent_id}/attrs/'

    try:

        response = requests.patch(url, body, headers=headers)
        print(response.status_code)
        print(response.text)
    except Exception as e:
        print("Something went wrong when requesting update:", e)
    
    return 


# In[ ]:


def InsertNewAttributesToentity(url, id, attr_list=None):

    ent = GetEntityByID(url, id)
    ent_id = ent['id']
    body = {}

    if attr_list is not None:
        for key in attr_list:
            try:
                ent[key] = attr_list[key]
            except Exception as e:
                print("Something went wrong while overwriting attributes:", e)
                break
        body = GenerateUpdatedBody(ent, attr_modified)
    else:
        attr_list = AddAttributes()
        body = json.loads(BuilEntityJSON(ent_id, ent['type'], attr_list, ent['@context']))
        body.pop('id')
        body.pop('type')
        body.pop('@context')
        body = json.dumps(body)

    headers = headers= {"Content-Type": "application/json",                         "Fiware-Service": FIWARE_SERVICE,                         "Fiware-ServicePath": FIWARE_SERVICEPATH                    }
    url = url+f'entities/{ent_id}/attrs/'

    try:

        response = requests.post(url, body, headers=headers)
        print(response.status_code)
        print(response.text)
    except Exception as e:
        print("Something went wrong when requesting update:", e)
    
    return 


# In[ ]:


CreateEntity(BASE_URL)


# In[ ]:


GetAllEntitiesV2(BASE_URL_V2)


# In[ ]:


InsertNewAttributesToentity(BASE_URL, "urn:ngsi-ld:TestForATTRS")


# In[ ]:




