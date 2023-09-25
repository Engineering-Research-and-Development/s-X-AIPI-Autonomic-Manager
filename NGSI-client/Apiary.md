# How to Use the NGSI-Client

## Prerequisites:

To use the client you need to have JSON library and requests library.
```
pip install requests
```

## How to use:

Import the library in your code

```python3
import OrionFunctions.py
```
Modify the following fields:

```python3
# Use IP and port of Orion
BASE_URL_V2 = "http://localhost:1026/v2/" 
BASE_URL = "http://localhost:1026/ngsi-ld/v1/"

# Change these values using the correct Orion tenant for your service.
FIWARE_SERVICE = "" # 
FIWARE_SERVICEPATH = "/"
```

Use the following schema to build your attribute list:

```python3
ATTR_MODIFIED_BODY = '''
"Attr_name" : { 
    "value" : val,
    "type" : Type,
    "metadata" : {}
}
'''
```


## API:

| Function                        | Description                                                                                                                                                  | Arguments                                                                                                                                                                                                                                                                                                                                                                 |
|---------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **GetAllEntitiesV2**            | Get the list of all entities ID. It is made in NGSI-v2 due to limitations imposed by NGSI-LD on all                                                          | **URL:** base url of Orion-NGSIv2 example: http://orionIP:orionPort/v2/                                                                                                                                                                                                                                                                                                     |
| **GetEntityByID**               | Get information from an entity in NGSI-LD                                                                                                                    | **URL**: base url of Orion-LD example: http://orionIP:orionPort/ngsi-ld/v1/ ; **id:** exact id of the entity                                                                                                                                                                                                                                                                    |
| **DeleteEntityByID**            | Deletes an entity in NGSI-LD                                                                                                                                 | same as above                                                                                                                                                                                                                                                                                                                                                             |
| **CreateEntity**                | Creates a new entity following two modes: - By passing arguments and building the body - By inserting values manually                                        | **(OPTIONAL) entity_id:** string ID of the entity, should be an URI. It is possible to use a name, it will be linked to a default uri; **(OPTIONAL) entity_type:** string containing type of an entity; **(OPTIONAL) attr_list** list of attributes in the format expressed in the "ATTR_MODIFIED_BODY" example  in the code; **(OPTIONAL) context:** string containing the context |
| **ModifyEntity**                | Modifies an entity by passing its id in the following two modes: - By passing the modified attribute list - By selecting which attributes to change manually |  **URL:** base url of Orion-LD, example as above; **id:** exact id of the entity; **(OPTIONAL) attr_modified:** list of attributes you wish to modify, formatted as the "ATTR_MODIFIED_BODY" example indicates                                                                                                                                                                     |
| **InsertNewAttributesToentity** | Insert new attributes to an entity following two modes: - By passing an attribute list - By inserting them manually                                          |  **URL:** base url of Orion-LD, example as above; **id:** exact id of the entity; **(OPTIONAL) attr_list:** list of attributes you wish to modify, formatted as the "ATTR_MODIFIED_BODY" example indicates                                                                                                                                                                         |

