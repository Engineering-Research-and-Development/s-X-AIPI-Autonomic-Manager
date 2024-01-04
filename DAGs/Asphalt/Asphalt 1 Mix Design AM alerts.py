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

f = open("/opt/airflow/dags/configs/asphalt.json", "r")
config = json.load(f)
f.close()


def list_configuration(**kwargs):
    
    conf_dict = {}
    ti = kwargs['ti']
    for key, value in kwargs['dag_run'].conf.items():
        conf_dict[key] = value
        
    print(conf_dict)
    ti.xcom_push(key="data", value=conf_dict)
    
    
    
def send_alert(**kwargs):

    ti = kwargs['ti']
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
    
    for alert in values:
        body["AM_Generated_Alarm"]["value"]["value"] = alert
        body["AM_Generated_Alarm"]["value"]["dateUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.patch(config['AM_Alert_Output_1'], headers=headers, data=json.dumps(body))
        print(r.status_code, r.text)
    
    
    
    
def check_RPA0700_sensor(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    val1 =  float(values['DataIngestion_production_t_RPBCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_RPA0700_max']["value"]["value"])

    if val1 > 0 and val2 == 0:
        return "RPA0700 Sensor Error"
    
    
    
    
def check_ST_Frames(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    val1 =  float(values['DataIngestion_production_t_STCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_t_SPCount']["value"]["value"])

    if val1 == 0 and val2 > 0:
        return "ST Frames Error"
        
    


def check_RT_Frames(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    val1 =  float(values['DataIngestion_production_t_RTCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_t_RPBCount']["value"]["value"])

    if val1 == 0 and val2 > 0:
        return "RT Frames Error"
    
    
    
def check_RPA2000_sensor(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA2000_min']["value"]["value"])

    if val1 < 0:
        return "RPA2000 Sensor Error"



def check_RPA2100_sensor(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA2100_min']["value"]["value"])

    if val1 < 0 or val1 > 255:
        return "RPA2100 Sensor Error"
        
        
def check_RPA1000_sensor(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_alert", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA1000_min']["value"]["value"])

    if val1 < 0:
        return "RPA1000 Sensor Error"

    
    
###############################################################################

with DAG(
	dag_id = 'asphalt_mix_design_monitoring',
	description = "Self-X Solution #1",
	default_args = default_args,
	start_date = datetime(2022, 11, 21, 11),
	schedule_interval = None
	
) as dag:



    task0 = PythonOperator(
    	task_id = "monitor_alert",
    	python_callable = list_configuration,
    	dag = dag,
    	provide_context = True
    )
    
    task_end = PythonOperator(
    	task_id = "send_alert",
    	python_callable = send_alert,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    task_ids = ["check_RPA0700_sensor", "check_ST_Frames", "check_RT_Frames", "check_RPA2000_sensor", "check_RPA2100_sensor", "check_RPA1000_sensor"]
    
    functions_dict = {
        'check_RPA0700_sensor': check_RPA0700_sensor,
        'check_ST_Frames': check_ST_Frames,
        'check_RT_Frames': check_RT_Frames,
        'check_RPA2000_sensor': check_RPA2000_sensor,
        'check_RPA2100_sensor': check_RPA2100_sensor,
        'check_RPA1000_sensor': check_RPA1000_sensor
    }
    
    for task in task_ids:
        
        t = PythonOperator(
    	    task_id = task,
    	    python_callable = functions_dict[task],
    	    dag = dag,
    	    provide_context = True
        )
        
        task0 >> t >> task_end
    


	
    
    
        
    

    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
