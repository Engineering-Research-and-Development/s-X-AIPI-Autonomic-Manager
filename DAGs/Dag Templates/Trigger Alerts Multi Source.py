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
	"owner" : "Owner",
	"retries" : 1,
	"retry_delay" : timedelta(seconds = 1)
}


# Configuration file, use to set variable names. Template provided 
fname = "trigger_alerts_multisource_config.json"
fpath = "/opt/airflow/dags/configs/" + fname
f = open(fpath, "r")
config = json.load(f)
f.close()


# Read configuration from DAG (an Orion subscription)
def list_configuration(**kwargs):
    
    conf_dict = {}
    ti = kwargs['ti']
    for key, value in kwargs['dag_run'].conf.items():
        conf_dict[key] = value
        
    print(conf_dict)
    ti.xcom_push(key="data", value=conf_dict)
    
    
    
    
# Update alert entity on Orion    
def send_alert(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids = task_ids)
    print(values)
        
    body = json.loads(''' 
    {
    "AM_Generated_Alarm": {
        "type": "Property",
        "value": {
            "value": "Test Update Alert",
            "dateUpdated": "2023-12-10T15:46:00Z"
        }
    }
    }''')
    body["@context"] = config["Alert_entity_context"]
    
    headers = {"Content-Type": "application/ld+json" }
    
    for alert in values:
        body["AM_Generated_Alarm"]["value"]["value"] = alert
        body["AM_Generated_Alarm"]["value"]["dateUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.patch(config['Alert_entity_uri'], headers=headers, data=json.dumps(body))
        print(r.status_code, r.text)
    
    
    
# A function for each "source" of alerts, with defined conditions. Add as more as needed.
def check_first_source(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    # Define attribute values
    val1 =  float(values['Attr_name_1']["value"]["value"])
    val2 =  float(values['Attr_name_2']["value"]["value"])
    
    #Define tresholds here
    if val1 > 0 and val2 == 0:
        return "First Source Error"
    
    
    
def check_second_source(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    val1 =  float(values['Attr_name_1']["value"]["value"])
    val2 =  float(values['Attr_name_3']["value"]["value"])

    if val1 == 0 and val2 > 0:
        return "Second Source Error"
        
    
def skip(**kwargs):
    return


   
    
###############################################################################

with DAG(
	dag_id = 'trigger_alerts_multi_source',
	description = "Triggering a list of alerts by checking several sources and types of errors",
	default_args = default_args,
	start_date = datetime(2024, 01, 15, 12),
	schedule_interval = None
	
) as dag:

    # Define task reading inputs
    task0 = PythonOperator(
    	task_id = "monitor_alert",
    	python_callable = list_configuration,
    	dag = dag,
    	provide_context = True
    )
    
    # Define Joining Task
    task_end = PythonOperator(
    	task_id = "send_alert",
    	python_callable = send_alert,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    # List of tasks (names of tasks, without spaces). Add as more as needed, matching defined functions above
    task_ids = ["check_first_source", "check_second_source", "..."]
    
    # Dictionary to link a task name to a function callback
    functions_dict = {
        'check_first_source': check_first_source,
        'check_second_source': check_second_source,
        '...': skip
    }
    
    # building dags dependencies
    for task in task_ids:
        
        t = PythonOperator(
    	    task_id = task,
    	    python_callable = functions_dict[task],
    	    dag = dag,
    	    provide_context = True
        )
        
        task0 >> t >> task_end
    


	
    
    
        
    

    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
