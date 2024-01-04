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


def list_configuration(**kwargs):
    
    conf_dict = {}
    ti = kwargs['ti']
    for key, value in kwargs['dag_run'].conf.items():
        conf_dict[key] = value
        
    print(conf_dict)
    ti.xcom_push(key="data", value=conf_dict)
    
    
    
    
def update_hitl(**kwargs):
    
    values = kwargs['data']
    
    yield(json.dumps(0), json.dumps(values))
    
    

    
    
    
    
###############################################################################

with DAG(
	dag_id = 'pharma_probe_position_HITL',
	description = "Self-X Solution #1 Outputs",
	default_args = default_args,
	start_date = datetime(2022, 11, 21, 11),
	schedule_interval = None
	
) as dag:



    task0 = PythonOperator(
    	task_id = "monitor_outputs",
    	python_callable = list_configuration,
    	dag = dag,
    	provide_context = True
    )
    
    
    task1 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="update_hitl",
        topic="pharma-alerts-solution1",
        producer_function=update_hitl,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids='monitor_outputs', key='data')}}"
        },
        poll_timeout=10
    )
    


    
    task0 >> task1
	
    
    
        
    

    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
