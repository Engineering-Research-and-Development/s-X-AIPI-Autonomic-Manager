# NGSI-LD Entities

In this folder are reported the interactions of the different s-X-AIPI domains (Aluminium, Asphalt, Steel and Pharma) with the AM in terms of OCB entities shared where they publish the context information (metadata) will be consumed.


## HITL Entities

The following section explains the use of HITL entities stored in the autonomic manager and how to interact with them, if necessary. Each subsection is dedicated to a specific use case with the related solutions.
Interacting with HITL entities requires the use of POST or PATCH APIs related to the entity. 

Consider the following scenario: it is necessary to update the NGSI-LD entity with:
- entity ID **urn:ngsi-ld:test_factory:001**
- attribute to modify:  **test_attribute**
- context:  **"https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"**

Then it is necessary to use the following endpoint using the **PATCH** HTTP Method:
```
http://136.243.156.113:1026/ngsi-ld/v1/entities/urn:ngsi-ld:sidenor_shorter_time_window:001/attrs
```
using the following body:

```json
{
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "test_attribute": {
        "type": "Property",
        "value": "NEW_VALUE"
        }
}
```
in case of multiple attributes, it is only sufficient to add more attributes in the payload

### Steel UC

#### Solution 1

Currently, the proposed solution is meant to provide information about scrap used in production. For this reason, a HITL entity was defined to check the awareness of the HITL operator about scrap introduction or removal. For this reason, parameters regarding the scrap presences are automatically created in the Autonomic Manager. To generate the attribute names explained below, it is necessary to extract the parameter name from the one used in the "small window" entity by removing the "_zeros" or "_max" ending particle, like the following schema:
```
transformation_lime_coke_limecoke01_zeros
```
:
```
transformation_lime_coke_limecoke01
```
So that the attributes needed for the HITL updates (in case of the above example parameter) are:

```
transformation_lime_coke_limecoke01_status 
transformation_lime_coke_limecoke01_confirmed
```


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
            "value": "Used/Not Used",
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
