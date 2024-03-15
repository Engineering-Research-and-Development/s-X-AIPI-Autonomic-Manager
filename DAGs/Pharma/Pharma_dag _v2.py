from airflow import DAG

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.decorators import dag, task
from airflow.utils.edgemodifier import Label
from airflow.providers.apache.kafka.operators.produce import ProduceToTopicOperator

import random
import re
import subprocess
import json
import requests

from datetime import datetime, timedelta


#Default parameters per operator:
default_args = {
	"owner" : "Emilio",
	"retries" : 1,
	"retry_delay" : timedelta(seconds = 1)
}

f = open("/opt/airflow/dags/configs/pharma.json", "r")
config = json.load(f)
f.close()


#################################################################################### GENERIC FUNCTIONS #################################################################################

def list_configuration(**kwargs):
    
    conf_dict = {}
    ti = kwargs['ti']
    for key, value in kwargs['dag_run'].conf.items():
        conf_dict[key] = value
        
    print(conf_dict)
    ti.xcom_push(key="data", value=conf_dict)
    
    
    
def add_param_to_body(body, param_name, param_value, now):

    if param_value is not None:
        body[param_name] = {}
        body[param_name]["type"] = "Property"
        body[param_name]["value"] = {}
        body[param_name]["value"]["value"] = param_value
        body[param_name]["value"]["dateUpdated"] = now
    
    return body
    
    
    
def create_alert_struct(alert):
    #sol, param, typ, cause, deviation, lower, upper
    pieces = alert.split("||")
    resp = {}
    
    body = json.loads(''' 
    {
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "AM_Generated_Alarm": {
        "type": "Property",
        "value": {
            "value": "Test Update Alert",
            "dateUpdated": "2023-12-10T15:46:00Z"
        }
    }
    }''')
    
    
    resp["solution"] = pieces[0]
    resp["attribute"] = pieces[1]
    resp["type"] = pieces[2]
    resp["cause"] = pieces[3]
    resp["deviation"] = pieces[4]
    resp["lowerThresh"] = pieces[5]
    resp["upperThresh"] = pieces[6]
    
    body["AM_Generated_Alarm"]["value"]["value"] = resp
    body["AM_Generated_Alarm"]["value"]["dateUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return body
    



def raise_alert(**kwargs):

    values = kwargs['data']
    
    values = values.split("'")
    values = [val for val in values if len(val) > 10]
    

    for alert in values:

        body = create_alert_struct(alert)
        yield(json.dumps(0), json.dumps(body))


##################################################################################### SOLUTION 1 FUNCTIONS ############################################################################


    
    
def analyze_position_status(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    

    position_status = values.get("DataIngestion_OCT_probePositionEvaluation", {}).get("value", {}).get("value", "")
    print(position_status)
    position_evaluation_alert = False
    
    if position_status == 0:
        position_evaluation_alert = True
    
    ti.xcom_push(key="prob_status_alert", value=position_evaluation_alert)
    
    

def analyze_position(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    print(values)
    
    position_x = values.get("DataIngestion_OCT_probePosition_xPos", {}).get("value", {}).get("value", 0)
    position_y = values.get("DataIngestion_OCT_probePosition_yPos", {}).get("value", {}).get("value", 0)
    print(position_x, position_y)
    
    position_alert = False
    
    if position_x < 400 or position_x > 900 or position_y < 50 or position_y > 200:
        position_alert = True
    
    ti.xcom_push(key="prob_alert", value=position_alert)
    

    
def update_position_status_output(**kwargs):

    ti = kwargs['ti']
    alert_status = ti.xcom_pull(task_ids="analyze_probe_position_status", key="prob_status_alert")
    alert_position = ti.xcom_pull(task_ids="analyze_probe_position", key="prob_alert")
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    position_x = values.get("DataIngestion_OCT_probePosition_xPos", {}).get("value", {}).get("value", 0)
    position_y = values.get("DataIngestion_OCT_probePosition_yPos", {}).get("value", {}).get("value", 0)
    
    
    body = json.loads('''
    {
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "DataIngestion_OCT_probePositionEvaluation": {
        "type": "Property",
        "value": {
            "value": 1,
            "dateUpdated": "2023-12-10T15:46:00Z"
        }
    },
    "DataIngestion_OCT_probePosition_yPos": {
        "type": "Property",
        "value": {
            "value": 0,
            "dateUpdated": "2023-12-10T15:46:00Z"
        }
    },
    "DataIngestion_OCT_probePosition_xPos": {
        "type": "Property",
        "value": {
            "value": 0,
            "dateUpdated": "2023-12-10T15:46:00Z"
        }
    }
    }
    ''')
    
    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    body["DataIngestion_OCT_probePositionEvaluation"]["value"]["dateUpdated"] = now
    body["DataIngestion_OCT_probePosition_yPos"]["value"]["dateUpdated"] = now
    body["DataIngestion_OCT_probePosition_xPos"]["value"]["dateUpdated"] = now
    
    body["DataIngestion_OCT_probePosition_yPos"]["value"]["value"] = position_y
    body["DataIngestion_OCT_probePosition_xPos"]["value"]["value"] = position_x
    
    '''
    if alert_status and not(alert_position):
        body["DataIngestion_OCT_probePositionEvaluation"]["value"]["value"] = "ok"
        r = requests.patch(config["output_1"], headers=headers, data=json.dumps(body))
    elif alert_position:
        body["DataIngestion_OCT_probePositionEvaluation"]["value"]["value"] = "not ok"
        r = requests.patch(config["output_1"], headers=headers, data=json.dumps(body))
    '''
    
    
    
    
    if alert_position:
        body["DataIngestion_OCT_probePositionEvaluation"]["value"]["value"] = 0
        r = requests.patch(config["output_1"], headers=headers, data=json.dumps(body))
        del body["@context"]
        return body
    else :
        r = requests.patch(config["output_1"], headers=headers, data=json.dumps(body))
        del body["@context"]
        return body
        
    print(json.dumps(body))
    


def execute_alert_hitl(**kwargs):

    values = kwargs['data']
    yield(json.dumps(0), json.dumps(values))
    
    


##################################################################################### SOLUTION 2 FUNCTIONS ############################################################################


def analyze_bad_images_ratio(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    alert_list = []
    
    for idx, attr in enumerate(config["solution_2_inputs_2"]):
        try:
            attr_val = float(values[attr]["value"]["value"])
            attr_upper_threshold_name = config["solution_2_thresholds_2"][idx]
            attr_upper_threshold = float(values[attr_upper_threshold_name]["value"]["value"])*0.1
            if attr_val > attr_upper_threshold:
                alert_list.append(f"2||{attr}||Bad Image Ratio||upper threshold||{attr_val}||None||{attr_upper_threshold}")
        except Exception as e:
            print(e)
            alert_list.append(f"2||{attr}||AM Error||AM ERROR occurred with variable||None||None||None")
                
    return alert_list
    
    


def analyze_max_signal_intensity(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    alert_list = []
    
    searched = config["solution_2_inputs_1"][0]
    sub1 = [re.search(searched, key, re.IGNORECASE) for key in values.keys()]
    
    if re.search("Pharma_alarms:001", values["id"], re.IGNORECASE) and any(sub1):
        try:
            attr = searched
            attr_val = values[attr]
            alert_list.append(f"2||{attr}||Signal Intensity Low||AI Methods||{attr_val}||None||None")
        except Exception as e:
            print(e)
            alert_list.append(f"2||{attr}||AM Error||AM ERROR occurred with variable||None||None||None")
                
    return alert_list

    
    
    
    
##################################################################################### SOLUTION 3 FUNCTIONS ############################################################################


def raise_HITL_IR_alert(**kwargs):
    
    values = kwargs['data']
    
    yield(json.dumps(0), json.dumps(values))
    
    
    

##################################################################################### SOLUTION 3 FUNCTIONS ############################################################################



def raise_HITL_power_supply_alert(**kwargs):
    
    values = kwargs['data']
    response = requests.get(config['output_attrs_4'])
    
    yield(json.dumps(0), json.dumps(values))
    
    

    
############################################################################### DAG & TASK DEFINITION ################################################################################################

with DAG(
	dag_id = 'pharma_dag',
	description = "Pharma Dag",
	default_args = default_args,
	start_date = datetime(2022, 11, 21, 11),
	schedule_interval = None
	
) as dag:


    # Read data from Server
    task_0_0 = PythonOperator(
    	task_id = "monitor_data",
    	python_callable = list_configuration,
    	dag = dag,
    	provide_context = True
    )
    
    
    # Decide Solution
    solution_options = ["solution_1", "solution_2", "solution_3", "solution_4", "solution_5", "skip_all_solutions"]
    
    @task.branch(task_id="decide_solution", provide_context = True, trigger_rule="none_failed")
    def decide_solution(choices, **kwargs):
        ti = kwargs['ti']
        values = ti.xcom_pull(task_ids="monitor_data", key="data")
        entity_name = values['id']
        
        sol1_keys = [key for key in values.keys() if "OCT_probe" in key]
        sol1_dict = {key: values[key] for key in sol1_keys}
    
        sol2_keys = [key for key in values.keys() if ("_OCT_signalQualityCheck_maxSignalIntensity" in key) or ("OCT_image" in key)]
        sol2_dict = {key: values[key] for key in sol2_keys}
    
        sol3_keys = [key for key in values.keys() if ("_IR_" in key)]
        sol3_dict = {key: values[key] for key in sol3_keys}
    
        sol4_keys = [key for key in values.keys() if ("_PWR_" in key)]
        sol4_dict = {key: values[key] for key in sol4_keys}
    
        sol5_keys = [key for key in values.keys() if ("RuntimeAIProcessing" in key)]
        sol5_dict = {key: values[key] for key in sol4_keys}
    
    
        if len(sol1_keys) == 3 and entity_name == config['small']:
            return choices[0]
        
        if len(sol2_keys) > 0:
            return choices[1]
        
        if len(sol3_keys) > 0:
            return choices[2]
        
        if len(sol4_keys) > 0:
            return choices[3]
        
        if len(sol5_keys) > 0:
            return choices[4]
        
        return choices[-1]
        
    task_0_1 = decide_solution(choices = solution_options)
    
    
    # Join after solution execution
    join_0 = EmptyOperator(
    	task_id = "join_end_dag",
    	trigger_rule="none_failed"
    )
    
    skip_0 = EmptyOperator(
    	task_id = "skip_all_solutions",
    )

    
    ######################### Solution 1 Taksks ################################
    
    
    task_1_0 = EmptyOperator(
    	task_id = "solution_1",
    )
    
    task_1_1 = PythonOperator(
    	task_id = "analyze_probe_position_status",
    	python_callable = analyze_position_status,
    	dag = dag,
    	provide_context = True
    )
    
    
    task_1_2 = PythonOperator(
    	task_id = "analyze_probe_position",
    	python_callable = analyze_position,
    	dag = dag,
    	provide_context = True
    )
    
    
    sol_1_options = ["execute_repositioning", "skip_1"]
    @task.branch(task_id="plan_action_1", provide_context = True, trigger_rule="all_success")
    def plan_action(choices, **kwargs):
        ti = kwargs['ti']
        alert_status = ti.xcom_pull(task_ids="analyze_probe_position_status", key="prob_status_alert")
        alert_position = ti.xcom_pull(task_ids="analyze_probe_position", key="prob_alert")
        
        previous_value = json.loads(requests.get(config["solution_1"]).text)["DataIngestion_OCT_probePositionEvaluation"]["value"]["value"]
        print(previous_value)
        
        if (previous_value == "ok" and alert_position) or (previous_value == "not ok"):
            return choices[0]

        return choices[0]
        
        
    task_1_3 = plan_action(choices= sol_1_options)
      
    
    join_1 = EmptyOperator(
    	task_id = "join_for_solution_1",
    	trigger_rule="none_failed"
    )
    
    task_1_4 = EmptyOperator(
	    task_id = "execute_repositioning"
	    )
    
    task_1_5 = PythonOperator(
	    task_id = "update_position_status",
	    python_callable = update_position_status_output,
	    provide_context = True,
	    dag = dag
	)
    
	
    task_1_6 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="execute_alert_hitl",
        topic="pharma-alerts-solution1",
        producer_function=execute_alert_hitl,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids='update_position_status')}}"
        },
        poll_timeout=10
    )
	
	
    skip_1 = EmptyOperator(
    	task_id = "skip_1",
    )
    
    
    ######################### Solution 2 Taksks ################################
	
    
    task_2_0 = EmptyOperator(
    	task_id = "solution_2",
    )
    
    
    task_2_1 = PythonOperator(
    	task_id = "analyze_bad_images_ratio",
    	python_callable = analyze_bad_images_ratio,
    	dag = dag,
    	provide_context = True
    )
    
    task_2_2 = PythonOperator(
    	task_id = "analyze_max_signal_intensity",
    	python_callable = analyze_max_signal_intensity,
    	dag = dag,
    	provide_context = True
    )
    

    
    task_2_4 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="execute_imaging_alert",
        topic="pharma-alerts-solution2",
        producer_function=raise_alert,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids=['analyze_bad_images_ratio', 'analyze_max_signal_intensity'])}}"
        },
        poll_timeout=10
    )
    
    
    
    sol_2_options = ["execute_imaging_alert", "skip_2"]
    @task.branch(task_id="plan_action_2", provide_context = True, trigger_rule="all_success")
    def plan_action(choices, **kwargs):

        ti = kwargs['ti']
        alert_bad_images = ti.xcom_pull(task_ids=['analyze_bad_images_ratio'])
        alert_signal_intensity = ti.xcom_pull(task_ids=['analyze_max_signal_intensity'])

        
        if len(alert_bad_images) > 0 or len(alert_signal_intensity) > 0:
            return choices[0]

        return choices[1]
        
        
        
    task_2_3 = plan_action(choices=sol_2_options)
    

    
    join_2 = EmptyOperator(
    	task_id = "join_for_solution_2",
    	trigger_rule="none_failed"
    )
    
	
    skip_2 = EmptyOperator(
    	task_id = "skip_2",
    )
    
    
    
    ######################### Solution 3 Taksks ################################
    
    task_3_0 = EmptyOperator(
    	task_id = "solution_3",
    )
    
    
    task_3_1 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="raise_HITL_IR_alert",
        topic="pharma-alerts-solution3",
        producer_function=raise_HITL_IR_alert,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids='monitor_data', key='data')}}"
        },
        poll_timeout=10
    )
    

    sol_3_options = ["raise_HITL_IR_alert", "skip_3"]   
    @task.branch(task_id="plan_action_3", provide_context = True, trigger_rule="all_success")
    def plan_action(choices, **kwargs):

        ti = kwargs['ti']
        values = ti.xcom_pull(task_ids="monitor_data", key="data")

        sub1 = [re.search("_IR_", key, re.IGNORECASE) for key in values.keys()]

        
        if any(sub1):
            return choices[0]
                
        return choices[-1]
        
    task_3_2 = plan_action(choices=sol_3_options)
      
    task_3_3 = EmptyOperator(
    	task_id = "analyze_IR_alert",
    )
    
    join_3 = EmptyOperator(
    	task_id = "join_for_solution_3",
    	trigger_rule="none_failed"
    )
    
	
    skip_3 = EmptyOperator(
    	task_id = "skip_3",
    )
    
    
    ######################### Solution 4 Taksks ################################
    
    task_4_0 = EmptyOperator(
    	task_id = "solution_4",
    )
    
    
    task_4_1 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="raise_HITL_power_supply_alert",
        topic="pharma-alerts-solution4",
        producer_function=raise_HITL_power_supply_alert,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids='monitor_data', key='data')}}"
        },
        poll_timeout=10
    )
    

    sol_4_options = ["raise_HITL_power_supply_alert", "skip_4"]   
    @task.branch(task_id="plan_action_4", provide_context = True, trigger_rule="all_success")
    def plan_action(choices, **kwargs):

        ti = kwargs['ti']
        values = ti.xcom_pull(task_ids="monitor_data", key="data")

        sub1 = [re.search("_IR_", key, re.IGNORECASE) for key in values.keys()]

        
        if any(sub1):
            return choices[0]
                
        return choices[-1]
        
    task_4_2 = plan_action(choices=sol_3_options)
      
    task_4_3 = EmptyOperator(
    	task_id = "analyze_power_supply_alert",
    )
    
    join_4 = EmptyOperator(
    	task_id = "join_for_solution_4",
    	trigger_rule="none_failed"
    )
    
	
    skip_4 = EmptyOperator(
    	task_id = "skip_4",
    )
    
    
    
    
    ############################################################################# TASK ORDERING ############################################################################################
    
    task_0_0 >> task_0_1
    task_0_1 >> task_1_0
    task_0_1 >> task_2_0
    task_0_1 >> task_3_0
    task_0_1 >> task_4_0
    task_0_0 >> skip_0 >> join_0

        
    task_1_0 >> [task_1_1, task_1_2] >> task_1_3 >> Label('Computing new positions') >> task_1_4 >> task_1_5 >> task_1_6 >> join_1
    task_1_0 >> [task_1_1, task_1_2] >> task_1_3 >> Label('Nothing to report') >> skip_1 >> join_1
    
    task_2_0 >> [task_2_1, task_2_2] >> task_2_3 >> task_2_4 >> join_2
    task_2_0 >> [task_2_1, task_2_2] >> task_2_3 >> skip_2 >> join_2
    
    task_3_0 >> task_3_3 >> task_3_2 >> task_3_1 >> join_3
    task_3_0 >> task_3_3 >> task_3_2 >> skip_3 >> join_3
    
    task_4_0 >> task_4_3 >> task_4_2 >> task_4_1 >> join_4
    task_4_0 >> task_4_3 >> task_4_2 >> skip_4 >> join_4
    
    join_1 >> join_0
    join_2 >> join_0
    join_3 >> join_0
    join_4 >> join_0
    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
