# NGSI-LD Entities

In this folder are reported the interactions of the different s-X-AIPI domains (Aluminium, Asphalt, Steel and Pharma) with the AM in terms of OCB entities shared where they publish the context information (metadata) will be consumed.


## HITL Entities

The following section explains the use of HITL entities stored in the autonomic manager and how to interact with them, if necessary. Each subsection is dedicated to a specific use case with the related solutions.
Interacting with HITL entities requires the use of POST or PATCH APIs related to the entity. 

Consider the following scenario: it is necessary to update the NGSI-LD entity with:
- entity ID **urn:ngsi-ld:test_factory:001**
- attribute:  **test_attribute**

Then it is necessary to use the following endpoint:
```
http://136.243.156.113:1026/ngsi-ld/v1/entities/urn:ngsi-ld:sidenor_shorter_time_window:001/attrs
```


### Steel UC

#### Solution 1

```json
{
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "id": "urn:ngsi-ld:sidenor_solution_HITL_Status_1:001",
    "type": "sidenor_HITL_Status",
    "Test_attribute_periods": {
        "type": "Property",
        "value": {
            "value": 0,
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    }, 
    "Test_attribute_status": {
        "type": "Property",
        "value": {
            "value": "Used/Not Used",
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    },
    "Test_attribute_previous": {
        "type": "Property",
        "value": {
            "value": "Used / Not Used",
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    },
    "Test_attribute_confirmed": {
        "type": "Property",
        "value": {
            "value": "Yes/No",
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    }
}

```
