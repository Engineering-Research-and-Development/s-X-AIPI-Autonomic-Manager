from airflow import DAG

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.decorators import dag, task
from airflow.utils.edgemodifier import Label
from airflow import settings
from airflow.models import Connection


import random
import json 
from utils.orionrcv import Start


from datetime import datetime, timedelta


#Default parameters per operator:
default_args = {
	"owner" : "Emilio",
	"retries" : 1,
	"retry_delay" : timedelta(seconds = 1)
}


def set_connection():


    conn = Connection(
            conn_id="kafka_broker",
            conn_type="kafka",
            extra = json.dumps({"socket.timeout.ms": 10, "bootstrap.servers": "136.243.156.113:9092"})
    ) #create a connection object
    session = settings.Session() # get the session
    session.add(conn)
    session.commit()


def start():

    a = Start()

    return a
    
    

#Scope del codice sarà nell'istanza di DAG
with DAG(
	dag_id = 'start_server',
	description = "Check dependencies and start receiver component for Airflow",
	default_args = default_args,
	start_date = datetime(2022, 11, 21, 11),
	schedule_interval = None
	
) as dag:


    task0 = BashOperator(
    	task_id = "install_kafka",
    	bash_command = 'pip install apache-airflow-providers-apache-kafka'
    )
    
    task_kafka= PythonOperator(
        task_id = "set_kafka_connection",
        python_callable = set_connection
    )
    
    task1 = PythonOperator(
        task_id = "start_server",
        python_callable= start
    )


        
    task0 >> task_kafka >>task1
   

    
    
    
    
    
    
    
    
