# Extend the AM functionalities
This guide wants to describe how to extend the AM functionalities.

For any issue in this guide, please feel free to open an issue.

## 1) Time for a new solution

Create a new module in the `dagster_service` folder, for example: `CustomSolution`.
Be sure that in this folder there are at least the `main.py` and the `__init__.py` like the following
```shell
.
├── __init__.py
└── main.py
```

This guide will not discuss about Dagster, thus in the `main.py` be sure to create a `@job` that will be called from orion_catcher

```python
@job
def process_custom(incoming_data, producer, service_config):
    # your business logic
```
Here you can implement your logic, handling the `incoming_data` from orion_catcher, the `producer`, which is the Kafka instance and `service_config` that contains all the configuration you can use in the solution development

Finally, it is necessary to declare the job in `__init__.py` file:
```python
from .main import process_custom

Definitions(jobs=[process_custom])
```

## 2) Include the new module into the dagster configuration

Edit the file `dagster_service/workspace.yaml` and append your `CustomSolution` module:
```yaml
  - python_module: CustomSolution
```

## 3) Define a configuration file for your solution

The first aspect to implement is to include the custom configuration. 
Fill this template with your needs and save it into `orion_catcher/additional_solution_configs`
```yaml
custom_solution:

  # Describe below the details to be used to correctly connect to the Orion server
  subscriptions:
    # The orion endpoint to use
    orion_endpoint:
    # The orion subscription endpoint
    subscription_ld_endpoint:
    # The context URI to use
    context:
    # Define the notification endpoint
    notification_endpoint: 
    # Additional information about the subscription (could be more than one)
    to_subscribe:
      - id:
        type:
        attrs: [ ]
        conditions: [ ]
      
 # Definition of the solution detail
  # The Kafka topic to use
  kafka_topic:
    
  # Dag parameters to be used 
  dag_config:
    # URL of the entities
    base_url:
    # Additional parameters that are going into the DAG
    useful_param_1:
    useful_param_2:
  
    # Definition of the actual solution
    solution_1:
      
      # Additional parameters
      useful_param_1:
      useful_param_2:
```
## 4) Catch the data from Orion
In `orion_catcher/main.py` append a new endpoint that enables orion_catcher to take the data from the orion.
Include the needed functionalities into the script file

```python
from dagster_service.CusomSolution.main import process_custom

@orion_catcher.post("/custom_solution")
async def custom_solution_handler(data: dict):
    result = process_custom.execute_in_process(input_values={"incoming_data": data,
                                                             "producer": producer,
                                                             "service_config": service_config["aluminium"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")
```
