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
http://136.243.156.113:1026/ngsi-ld/v1/entities/urn:ngsi-ld:urn:ngsi-ld:test_factory:001/attrs
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

Following, the entity structure related to the HITL for Solution 1 with the allowed values.


```json
{
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "id": "urn:ngsi-ld:sidenor_solution_HITL_Status_1:001",
    "type": "sidenor_HITL_Status",
    "Test_attribute_status": {
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

- Attributes ending with **"_confirmed"** are used for telling the autonomic manager that the HITL operator received the alert related to the attribute name.
- Attributes ending with **"_status"** are used for telling the autonomic manager if the related material is currently used or not. In combination with the "_confirmed" attribute, it serves to aknowledge the AM of alerting reception and confirmation of the production status.
  
Using the above example, a possible **PATCH** update for this entity may be:
URL
```
http://136.243.156.113:1026/ngsi-ld/v1/entities/urn:ngsi-ld:sidenor_solution_HITL_Status_1:001/attrs
```
```json
{
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "transformation_lime_coke_limecoke01_status": {
        "type": "Property",
        "value": {
            "value": "Used",
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    },
    "transformation_lime_coke_limecoke01_confirmed": {
        "type": "Property",
        "value": {
            "value": "Yes",
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    }
}
```
This example tells the autonomic manager that the HITL operator received a notification (for example, limecoke01 was introduced in pipeline) and confirmed that limecoke01 is currently used in production (confirmed normal behaviour), so that the AM should not alert the operator again while in this status.



#### Solution 2

The proposed solution aims to check anomalies in exploration data. The HITL entity is used to store information about aknowledgment of anomalies on behalf of the operator. With respect to Solution1, here attribute names are built by taking the whole name of related "small window" parameter without cutting the last particle.

For simplicity, it is only reported the entity structure and attribute meanings:

```json
{
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "id": "urn:ngsi-ld:sidenor_solution_HITL_Status_2:001",
    "type": "sidenor_HITL_Status",
    "Test_attribute_HITL_anomalies_confirmation": {
        "type": "Property",
        "value": {
            "value": "Unconfirmed/Confirmed_Anomalies/Confirmed_Normal",
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    }
}
```
Possible values for "_Status" are:
- **Unconfirmed**: the alarm does not exist / was sent but HITL has not confirmed yet
- **Confirmed_Anomalies** the HITL operator received an alarm and aknowledged the AM of an existing anomaly
- **Confirmed_Normal** the HITL operator received an alarm and aknowledged the AM of a normal behaviour



#### Solution 3

The proposed solution checks if Mean Absolute Error of the AI model is in defined thresholds related to predicted parameter.
In this structure, only this attribute is selected, so attribute name should not be built

```json
{
    "modeling_LinearRegression_MAE_confirmed": {
        "type": "Property",
        "value": {
            "value": "Yes/No",
            "dateUpdated": "2024-2-26T11:46:00Z"
        }
    }
}
```
Possible values for "_confirmed" are:
- **No**: the alarm does not exist / was sent but HITL has not confirmed yet
- **Yes** the HITL operator received an alarm



#### Solution 4

Solution 4 does not need any HITL entity
