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


#################################################################################### GENERIC FUNCTIONS #################################################################################

def list_configuration(**kwargs):
    
    conf_dict = {}
    ti = kwargs['ti']
    for key, value in kwargs['dag_run'].conf.items():
        conf_dict[key] = value
        
    print(conf_dict)
    ti.xcom_push(key="data", value=conf_dict)
    


##################################################################################### SOLUTION 1 FUNCTIONS ############################################################################



def send_alert_solution1(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids = task_ids_solution1)
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
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_t_RPBCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_RPA0700_max']["value"]["value"])

    if val1 > 0 and val2 == 0:
        return "RPA0700 Sensor Error"
    
    
    
    
def check_ST_Frames(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_t_STCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_t_SPCount']["value"]["value"])

    if val1 == 0 and val2 > 0:
        return "ST Frames Error"
        
    


def check_RT_Frames(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_t_RTCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_t_RPBCount']["value"]["value"])

    if val1 == 0 and val2 > 0:
        return "RT Frames Error"
    
    
    
def check_RPA2000_sensor(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA2000_min']["value"]["value"])

    if val1 < 0:
        return "RPA2000 Sensor Error"



def check_RPA2100_sensor(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA2100_min']["value"]["value"])

    if val1 < 0 or val1 > 255:
        return "RPA2100 Sensor Error"
        
        
def check_RPA1000_sensor(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA1000_min']["value"]["value"])

    if val1 < 0:
        return "RPA1000 Sensor Error"
    
   
    


##################################################################################### SOLUTION 2 FUNCTIONS ############################################################################


    
    
    
##################################################################################### SOLUTION 3 FUNCTIONS ############################################################################


    

##################################################################################### SOLUTION 4 FUNCTIONS ############################################################################



    
############################################################################### DAG & TASK DEFINITION ################################################################################################

with DAG(
	dag_id = 'asphalt_dag',
	description = "Asphalt Dag",
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
        
        sol1_keys = config["solution_1_inputs"]
        sol1_dict = {key: values[key] for key in sol1_keys}
    
        sol2_keys = [key for key in values.keys() if ("_OCT_signalQualityCheck_maxSignalIntensity" in key) or ("OCT_image" in key)]
        sol2_dict = {key: values[key] for key in sol2_keys}
    
        sol3_keys = [key for key in values.keys() if ("_IR_" in key)]
        sol3_dict = {key: values[key] for key in sol3_keys}
    
        sol4_keys = [key for key in values.keys() if ("_PWR_" in key)]
        sol4_dict = {key: values[key] for key in sol4_keys}
    
        sol5_keys = [key for key in values.keys() if ("RuntimeAIProcessing" in key)]
        sol5_dict = {key: values[key] for key in sol4_keys}
    
    
        if len(sol1_dict) == len(sol1_keys) and entity_name == config['small']:
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
    
    task_1_2 = PythonOperator(
    	task_id = "send_alert_solution1",
    	python_callable = send_alert_solution1,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    task_ids_solution1 = ["check_RPA0700_sensor", "check_ST_Frames", "check_RT_Frames", "check_RPA2000_sensor", "check_RPA2100_sensor", "check_RPA1000_sensor"]
    
    functions_dict_solution1 = {
        'check_RPA0700_sensor': check_RPA0700_sensor,
        'check_ST_Frames': check_ST_Frames,
        'check_RT_Frames': check_RT_Frames,
        'check_RPA2000_sensor': check_RPA2000_sensor,
        'check_RPA2100_sensor': check_RPA2100_sensor,
        'check_RPA1000_sensor': check_RPA1000_sensor
    }
    
    tasks_1 = []
    for task in task_ids_solution1:
        
        t_1_1 = PythonOperator(
    	    task_id = task,
    	    python_callable = functions_dict_solution1[task],
    	    dag = dag,
    	    provide_context = True
        )
        
        tasks_1.append(t_1_1)
	
    
    
    
    ######################### Solution 2 Taksks ################################
	
    
    task_2_0 = EmptyOperator(
    	task_id = "solution_2",
    )
    
      
    
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
    task_0_1 >> skip_0 >> join_0

        
    task_1_0 >> tasks_1 >> task_1_2
    
    #task_2_0 >> task_2_4 >> task_2_3 >> task_2_1 >> join_2
    #task_2_0 >> task_2_4>> task_2_3 >> task_2_2 >> join_2
    #task_2_0 >> task_2_4 >> task_2_3 >> skip_2 >> join_2
    
    #task_3_0 >> task_3_3 >> task_3_2 >> task_3_1 >> join_3
    #task_3_0 >> task_3_3 >> task_3_2 >> skip_3 >> join_3
    
    #task_4_0 >> task_4_3 >> task_4_2 >> task_4_1 >> join_4
    #task_4_0 >> task_4_3 >> task_4_2 >> skip_4 >> join_4
    
    task_1_2 >> join_0
    #join_2 >> join_0
    #join_3 >> join_0
    #join_4 >> join_0
    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
