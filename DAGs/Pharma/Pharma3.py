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
    
    
    
    
def alert_HITL(**kwargs):
    
    values = kwargs['data']
    #response = requests.get(config['output_attrs_3'])
    
    yield(json.dumps(0), json.dumps(values))
    
    
    
    
    
    
###############################################################################

with DAG(
	dag_id = 'pharma_IR_data_integrity_alerts',
	description = "Self-X Solution #3",
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
    
    
    task1 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="alert_HITL",
        topic="pharma-alerts-solution3",
        producer_function=alert_HITL,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids='monitor_alert', key='data')}}"
        },
        poll_timeout=10
    )
    

    options = ["alert_HITL", "skip"]

    
    @task.branch(task_id="plan_action", provide_context = True, trigger_rule="all_done")
    def plan_action(choices, **kwargs):

        ti = kwargs['ti']
        values = ti.xcom_pull(task_ids="monitor_alert", key="data")

        sub1 = [re.search("_IR_", key, re.IGNORECASE) for key in values.keys()]

        
        if any(sub1):
            return options[0]
                
        return options[-1]
        
    branch = plan_action(choices= options)
      
    
    join = EmptyOperator(
    	task_id = "join_after_choice",
    	trigger_rule="all_done"
    )
    
	
    skip = EmptyOperator(
    	task_id = "skip",
    )
    
    task0 >> branch >> task1 >> join
    task0 >> branch >> skip >> join
	
    
    
        
    

    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
