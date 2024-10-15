# Extend the AM functionalities
This guide wants to describe how to extend the AM functionalities.

For any issue in this guide, please feel free to open an issue.

## 1) Define a new solution

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

  # Section describing connection details to the Orion server for data subscriptions
  subscriptions:

    # The main endpoint of the Orion Context Broker, used to interact with the Orion server.
    orion_endpoint:
    # Example: "http://136.243.156.113:1026/ngsi-ld/v1/subscriptions/"

    # The specific endpoint for managing subscriptions within the Orion Context Broker.
    subscription_ld_endpoint:
    # Example: "http://136.243.156.113:1026/ngsi-ld/v1/subscriptions"

    # The context URI identifies the relevant data model context that Orion will use.
    context:
    # Example: "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

    # The endpoint to which Orion will send notifications when there are changes in subscribed data.
    notification_endpoint:
    # Example:  ":8001/aluminium"

    # Details about entities to subscribe to, including conditions for the subscription.
    to_subscribe:
      # This can include multiple entities or data types that you want Orion to monitor.
      - id:
        # The unique identifier of the entity to subscribe to. 
        # Example: "urn:ngsi-ld:IDALSA_smaller_time_window:001"

        type:
        # The entity type you are subscribing to (e.g., 'Store', 'Vehicle').
        # Example: "factory"

        attrs: [ ]
          # A list of specific attributes that you want to subscribe to (e.g., 'temperature', 'location').

        conditions: [ ]
          # Specify conditions for triggering notifications (e.g., attribute changes, threshold values).
          # Example: 
            # - "temperature > 30"
            # - "status == 'open'"

  # Defines the configuration for connecting to Kafka, which will receive messages or events.
  kafka_topic:
  # The name of the Kafka topic where the messages should be published.
  # Example: "aluminium"

  # Parameters for configuring Directed Acyclic Graph (DAG) tasks, used to manage workflows.
  dag_config:

    # The base URL where entities are managed or fetched (for API calls within the DAG tasks).
    base_url:
    # Example: "http://136.243.156.113:1026/ngsi-ld/v1/entities/"

    # Additional custom parameters that may be required for DAG configuration.
    useful_param_1:
    # Example:  small_window: "urn:ngsi-ld:IDALSA_smaller_time_window:001"

    useful_param_2:
    # Example: large_window: "urn:ngsi-ld:IDALSA_greater_time_window:001"

    # Configuration of a specific solution using these parameters (this can be extended with other solutions).
    solution_1:

      # Any additional parameters specific to this solution.
      # Parameters are solution-specific to the solution, but the following example parameters may be useful:

      alarm_type:
      # String containing the alarm type to raise. 
      # Example: alarm_type_heats: "Heat Length Error"

      inputs:
      # List of OCB attributes for the monitored source. 
      # Example: inputs_AI: [ "ModelTraining_CA_Accuracy", "ModelTraining_MP_Accuracy", "ModelTraining_MT_Accuracy", "ModelTraining_MA_Accuracy" ]
      upper_thresholds:
      # List of float values. These thresholds are used to compare attributes from inputs to threshold values. Use 999999.9 to set "+inf"
      # Example: upper_thresholds_AI: [ 999999.9, 999999.9, 999999.9, 999999.9 ]
      lower_thresholds:
      # List of float values. These thresholds are used to compare attributes from inputs to threshold values. Use -999999.9 to set "-inf"
      # Example: lower_thresholds_AI: [ 70.0, 70.0, 70.0, 70.0 ]

      # Alternative Threshold (OCB Max/Min Attribute):
      Threshold Attribute:
      # Use an OCB attribute to set thresholds
      max_attribute:
      # Example: max_value: ["ModelTraining_CA_Accuracy_maxDesiredValue"]
      min_attribute:
      # Example: low_value: ["ModelTraining_CA_Accuracy_minDesiredValue"]

      # Alternative Threshold (OCB Attribute + percent change):
      # Use an OCB value to set a particular baseline + a percentage change based on this value
      reference_value:
      # Use a OCB attribute to set a value, pass as list
      # Example: base_value: ["ModelTraining_CA_Accuracy_baseVal"]
      threshold_pct_change:
      # List of float numbers to set a percentage to apply to reference value.
      # Example: pct_change_coeff: [10.0]
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
## 5) Enable the new module in the Docker-compose
The last step involves to enable of the module in the docker compose file.
To do so, you can un-comment the part that binds the `additional_solutions` to the container:
```yaml
    volumes:
      - ./solution_configs:/orion_catcher/additional_solution_configs
```
