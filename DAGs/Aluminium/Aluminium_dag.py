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
import numpy as np

from datetime import datetime, timedelta


#Default parameters per operator:
default_args = {
	"owner" : "Emilio",
	"retries" : 1,
	"retry_delay" : timedelta(seconds = 1)
}

f = open("/opt/airflow/dags/configs/aluminium.json", "r")
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
    resp["solution"] = pieces[0]
    resp["attribute"] = pieces[1]
    resp["type"] = pieces[2]
    resp["cause"] = pieces[3]
    resp["deviation"] = pieces[4]
    resp["lowerThresh"] = pieces[5]
    resp["upperThresh"] = pieces[6]
    
    return resp
    


def notify_anomalies(**kwargs):

    ti = kwargs['ti']
    task_ids = kwargs["tasks"]

    values = ti.xcom_pull(task_ids = task_ids)
    print(values)
        
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
    
    headers = {"Content-Type": "application/ld+json" }
    
    l = []
    for lists in values:
        if type(lists) == type(["list"]):
            l.extend(lists)
        elif type(lists) == type("string"):
            l.append(lists)
    
    
    for alert in l:
        alert_val = create_alert_struct(alert)
        body["AM_Generated_Alarm"]["value"]["value"] = alert_val
        body["AM_Generated_Alarm"]["value"]["dateUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.patch(config['AM_Alert_Output'], headers=headers, data=json.dumps(body))
        print(r.status_code, r.text)
    return
    
    
##################################################################################### SOLUTION 1 FUNCTIONS ############################################################################





##################################################################################### SOLUTION 2 FUNCTIONS ############################################################################

def check_heats_duration(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    alert_list = []
    
    for idx, attr in enumerate(config["solution_2_inputs_1"]):
        try:
            attr_val = float(values[attr]["value"]["value"])
            attr_upper_threshold = config["solution_2_thresholds_1"][idx]
            #sol, param, typ, cause, deviation, lower, upper
            if attr_val > attr_upper_threshold:
                alert_list.append(f"2||{attr}||Heat Length Issues||upper threshold||{attr_val}||None||{attr_upper_threshold}")
        except Exception as e:
            print(e)
            alert_list.append(f"2||{attr}||AM Error||AM ERROR occurred with variable||None||None||None")
                
    return alert_list
    
    
    
def check_material_deviation(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    alert_list = []
    
    url = config["base_url"] + "entities/" + config["large"]
    entity = requests.get(url).json()
    
    for idx, attr in enumerate(config["solution_2_inputs_2"]):
        try:
            attr_val = float(values[attr]["value"]["value"])
            attr_large_val = float(entity[attr]["value"]["value"])
            
            pct_change = config["solution_2_pct_change"][0]/100
            attr_range = np.abs(attr_large_val)*pct_change
            attr_lower_threshold = attr_large_val - attr_range
            attr_upper_threshold = attr_large_val + attr_range
            
            if attr_val > attr_upper_threshold:
                alert_list.append(f"2||{attr}||Material Deviation Detected||upper threshold||{attr_val}||{attr_lower_threshold}||{attr_upper_threshold}")
            elif attr_val < attr_lower_threshold:
                alert_list.append(f"2||{attr}||Material Deviation Detected||lower threshold||{attr_val}||{attr_lower_threshold}||{attr_upper_threshold}")
        except Exception as e:
            print(e)
            alert_list.append(f"2||{attr}||AM Error||AM ERROR occurred with variable||None||None||None")
                
    return alert_list
    

    
##################################################################################### SOLUTION 3 FUNCTIONS ############################################################################



def check_human_satisfation(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    alert_list = []
    
    for idx, attr in enumerate(config["solution_3_inputs"]):
        try:
            attr_val = float(values[attr]["value"]["value"])
            attr_lower_threshold = config["solution_3_thresholds"][idx]
            if attr_val < attr_lower_threshold:
                alert_list.append(f"3||{attr}||Human Dissatisfaction Detected||lower threshold||{attr_val}||{attr_lower_threshold}||None")
        except Exception as e:
            print(e)
            alert_list.append(f"3||{attr}||AM Error||AM ERROR occurred with variable||None||None||None")
                
    return alert_list



##################################################################################### SOLUTION 4 FUNCTIONS ############################################################################





    
##################################################################################### DAG & TASK DEFINITION ###########################################################################


with DAG(
	dag_id = 'aluminium_dag',
	description = "Aluminium Dag",
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
    
    
    solutions = ["sub_solution_1", "sub_solution_2", "sub_solution_3", "sub_solution_4"]
    @task.branch(task_id="decide_solution", provide_context = True, trigger_rule="all_success")
    def decide_solution(choices, **kwargs):
        ti = kwargs['ti']
        value = ti.xcom_pull(task_ids="monitor_data", key="data")
        
        if value['id'] == config["small"]:
            if config["solution_2_inputs_1"][0] in list(value.keys()):
                return choices[1]
        elif value['id'] == config["large"]:
            if config["solution_3_inputs"][0] in list(value.keys()):
                return choices[2]

        return choices[0]
        
    task_0_1 = decide_solution(choices = solutions)

    
    # Join after solution execution
    join_0 = EmptyOperator(
    	task_id = "join_end_dag",
    	trigger_rule="all_success"
    )
    
    skip_0 = EmptyOperator(
    	task_id = "skip_all_solutions",
    )
        
    
    ######################### Solution 1 Taksks ################################
    
    
    task_1_0 = EmptyOperator(
    	task_id = "sub_solution_1",
    )
    
           
    
    join_1 = EmptyOperator(
    	task_id = "join_for_solution_1",
    	trigger_rule="all_success"
    )
    
	
    
    
    
    ######################### Solution 2 Taksks ################################
	
    
    task_2_0 = EmptyOperator(
    	task_id = "sub_solution_2",
    )
    
    
    task_2_1 = PythonOperator(
    	task_id = "check_heats_duration",
    	python_callable = check_heats_duration,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='all_success'
    )
    
    
    task_2_2 = PythonOperator(
    	task_id = "check_material_deviation",
    	python_callable = check_material_deviation,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='all_success'
    )
    

    
    
    sol_2_options = ["execute_alerting_2", "skip_2"]
    @task.branch(task_id="plan_action_2", provide_context = True, trigger_rule="all_success")
    def plan_action_2(choices, **kwargs):
        ti = kwargs['ti']
        alert_duration = ti.xcom_pull(task_ids="check_heats_duration")
        alert_deviation = ti.xcom_pull(task_ids="check_material_deviation")
        
        if len(alert_duration) > 0 or len(alert_deviation) > 0:
            return choices[0]

        return choices[1]
     
    
    task_2_3 = plan_action_2(choices=sol_2_options)
    
    
    task_2_4 = PythonOperator(
    	task_id = sol_2_options[0],
    	python_callable = notify_anomalies,
    	op_kwargs = {"tasks" : ["check_heats_duration", "check_material_deviation"]},
    	dag = dag,
    	provide_context = True,
    	trigger_rule='all_success'
    )
    
    
    
    skip_2 = EmptyOperator(
    	task_id = "skip_2",
    	trigger_rule="all_success"
    )
      
    
    join_2 = EmptyOperator(
    	task_id = "join_for_solution_2",
    	trigger_rule="none_failed"
    )
    

    
    
    ######################### Solution 3 Taksks ################################
    
    task_3_0 = EmptyOperator(
    	task_id = "sub_solution_3",
    )
    
    
    task_3_1 = PythonOperator(
    	task_id = "check_human_satisfation",
    	python_callable = check_human_satisfation,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='all_success'
    )
    
    sol_3_options = ["execute_alerting_3", "skip_3"]
    @task.branch(task_id="plan_action_3", provide_context = True, trigger_rule="all_success")
    def plan_action_3(choices, **kwargs):
        ti = kwargs['ti']
        alert_satisfaction = ti.xcom_pull(task_ids="check_human_satisfation")
        
        if len(alert_satisfaction) > 0:
            return choices[0]

        return choices[1]
        
   
   
    task_3_2 = plan_action_3(choices=sol_3_options)
    
    
    task_3_3 = PythonOperator(
    	task_id = sol_3_options[0],
    	python_callable = notify_anomalies,
    	op_kwargs = {"tasks" : ["check_human_satisfation"]},
    	dag = dag,
    	provide_context = True,
    	trigger_rule='all_success'
    )
    
    skip_3 = EmptyOperator(
    	task_id = "skip_3",
    	trigger_rule="all_success"
    )
    
    join_3 = EmptyOperator(
    	task_id = "join_for_solution_3",
    	trigger_rule="none_failed"
    )
    

    
    ######################### Solution 4 Taksks ################################
    
    task_4_0 = EmptyOperator(
    	task_id = "sub_solution_4",
    )
    
   
    
    
    join_4 = EmptyOperator(
    	task_id = "join_for_solution_4",
    	trigger_rule="all_success"
    )
    

    
    
    
    
    ############################################################################# TASK ORDERING ############################################################################################
    
    
    
    task_0_0 >> task_0_1 >> [task_1_0, task_2_0, task_3_0, task_4_0, skip_0]

        
    task_1_0 >> join_1
     
    task_2_0 >> [task_2_1 , task_2_2] >> task_2_3 
    task_2_3 >> skip_2 >> join_2
    task_2_3 >> task_2_4 >> join_2
    
    task_3_0 >> task_3_1 >> task_3_2
    task_3_2 >> skip_3 >> join_3
    task_3_2 >> task_3_3 >> join_3

    task_4_0 >> join_4
    
    
    join_1 >> join_0
    join_2 >> join_0
    join_3 >> join_0
    join_4 >> join_0
    skip_0 >> join_0
    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
