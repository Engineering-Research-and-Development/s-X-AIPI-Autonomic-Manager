from airflow import DAG

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.decorators import dag, task
from airflow.utils.edgemodifier import Label

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



def list_configuration(**kwargs):
    
    conf_dict = {}
    ti = kwargs['ti']
    for key, value in kwargs['dag_run'].conf.items():
        conf_dict[key] = value
        
    print(conf_dict)
    ti.xcom_push(key="data", value=conf_dict)
    
    
    
def analyze_position_status(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    

    position_status = values.get("DataIngestion_OCT_probePositionEvaluation", {}).get("value", {}).get("value", "")
    print(position_status)
    position_evaluation_alert = False
    
    if "not" in position_status:
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
            "value": "ok",
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
    
    previous_value = json.loads(requests.get(config["solution_1"]).text)["DataIngestion_OCT_probePositionEvaluation"]["value"]["value"]
    print(previous_value)
    
    
    if previous_value == "ok" and alert_position:
        body["DataIngestion_OCT_probePositionEvaluation"]["value"]["value"] = "not ok"
        r = requests.patch(config["output_1"], headers=headers, data=json.dumps(body))
    elif previous_value == "not ok" and alert_position:
        body["DataIngestion_OCT_probePositionEvaluation"]["value"]["value"] = "not ok"
        r = requests.patch(config["output_1"], headers=headers, data=json.dumps(body))
    elif previous_value == "not ok" and not alert_position:
        r = requests.patch(config["output_1"], headers=headers, data=json.dumps(body))
        
    print(json.dumps(body))
    


    return

        
    
    
    
    
    
###############################################################################

with DAG(
	dag_id = 'pharma_probe_position_evaluation',
	description = "Self-X Solution #1",
	default_args = default_args,
	start_date = datetime(2022, 11, 21, 11),
	schedule_interval = None
	
) as dag:



    task0 = PythonOperator(
    	task_id = "monitor_data",
    	python_callable = list_configuration,
    	dag = dag,
    	provide_context = True
    )
    
    task1 = PythonOperator(
    	task_id = "analyze_probe_position_status",
    	python_callable = analyze_position_status,
    	dag = dag,
    	provide_context = True
    )
    
    
    task2 = PythonOperator(
    	task_id = "analyze_probe_position",
    	python_callable = analyze_position,
    	dag = dag,
    	provide_context = True
    )
    
    options = ["execute_repositioning", "skip"]

    
    @task.branch(task_id="plan_action", provide_context = True, trigger_rule="all_done")
    def plan_action(choices, **kwargs):
        ti = kwargs['ti']
        alert_status = ti.xcom_pull(task_ids="analyze_probe_position_status", key="prob_status_alert")
        alert_position = ti.xcom_pull(task_ids="analyze_probe_position", key="prob_alert")
        
        if alert_position or alert_status:
            return options[0]

        return options[0]
        
    task3 = plan_action(choices= options)
      
    
    join = EmptyOperator(
    	task_id = "join_after_choice",
    	trigger_rule="none_failed"
    )
    
    task4 = EmptyOperator(
	    task_id = "execute_repositioning"
	    )
    
    task5 = PythonOperator(
	    task_id = "update_position_status",
	    python_callable = update_position_status_output,
	    provide_context = True,
	    dag = dag
	)
    
	
    task6 = BashOperator(
	    task_id = "execute_alert_hitl",
	    bash_command = 'echo Saving Results'
	)
	
    skip = EmptyOperator(
    	task_id = "skip",
    )
	
    
    
    task0 >> [task1, task2] >> task3 >> Label('Computing new positions') >> task4 >> [task6, task5] >> join
    task0 >> [task1, task2] >> task3 >> Label('Nothing to report') >> skip >> join
        
    

    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
