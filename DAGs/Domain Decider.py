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

from datetime import datetime, timedelta

import utils.orionrcv as rcv


#Default parameters per operator:
default_args = {
	"owner" : "Emilio",
	"retries" : 1,
	"retry_delay" : timedelta(seconds = 1)
}



################################################################# Pharma Section

def trigger_pharma_monitoring(values):
   
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
    
    if len(sol1_keys) == 3:
        command = '''airflow dags trigger pharma_probe_position_evaluation -c ' ''' + json.dumps(sol1_dict) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
    if len(sol2_keys) == 3:
        command = '''airflow dags trigger pharma_solution2 -c ' ''' + json.dumps(sol2_dict) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
    if len(sol3_keys) == 3:
        command = '''airflow dags trigger pharma_solution3 -c ' ''' + json.dumps(sol3_dict) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
    if len(sol4_keys) == 2:
        command = '''airflow dags trigger pharma_solution4 -c ' ''' + json.dumps(sol4_dict) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
    if len(sol5_keys) == 5:
        command = '''airflow dags trigger pharma_solution5 -c ' ''' + json.dumps(sol5_dict) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
    return
    
    
    
def trigger_pharma_alarms(values):
    
    
    sol2_keys = [key for key in values.keys() if ("_OCT_signalQualityCheck_maxSignalIntensity" in key) or ("OCT_image" in key)]
    sol3_keys = [key for key in values.keys() if ("_IR_" in key)]
    sol4_keys = [key for key in values.keys() if ("_PWR_" in key)]
    
    if len(sol2_keys) > 0:
        command = '''airflow dags trigger pharma_oct_signal_quality_alerts -c ' ''' + json.dumps(values) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
    if len(sol3_keys) > 0:
        command = '''airflow dags trigger pharma_IR_data_integrity_alerts -c ' ''' + json.dumps(values) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
        
    if len(sol4_keys) > 0:
        command = '''airflow dags trigger pharma_power_supply_chain_alerts -c ' ''' + json.dumps(values) + ''' ' '''
        print(command)
        subprocess.run(command, shell=True, check=True)
    
    
    
    
def trigger_pharma_outputs(values):
    return
    
    
    
def trigger_pharma(**kwargs):
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="read_data", key="data")    
    
    entity_name = values["id"]
    
    if re.search("alarm", entity_name, re.IGNORECASE):
       trigger_pharma_alarms(values)
    elif re.search("solution_output", entity_name, re.IGNORECASE):
       trigger_pharma_outputs(values)
    else:
       trigger_pharma_monitoring(values)
    
 
################################################################# Steel Section       

def trigger_steel(**kwargs):
    
    return
    

################################################################# Aluminium Section    

def trigger_aluminium(**kwargs):
    
    return
    
################################################################# Asphalt Section
    
def trigger_asphalt(**kwargs):
    
    return
    
################################################################# Configuration Read

def list_configuration(**kwargs):
    
    conf_dict = {}
    ti = kwargs['ti']
    for key, value in kwargs['dag_run'].conf.items():
        conf_dict[key] = value
        
    print(conf_dict)
    ti.xcom_push(key="data", value=conf_dict)
    
    

################################################################# DAG

with DAG(
	dag_id = 'solution_triggerer',
	description = "Understand Domain",
	default_args = default_args,
	start_date = datetime(2022, 11, 21, 11),
	schedule_interval = None
	
) as dag:



    task0 = PythonOperator(
    	task_id = "read_data",
    	python_callable = list_configuration,
    	dag = dag,
    	provide_context = True
    )
    
    options = ["pharma", "sidenor", "asphalt", "idalsa", "skip"]
    labels = ["Launch Pharma", "Launch Steel", "Launch Asphalt", "Launch Aluminium", "Skip"]
    
    @task.branch(task_id="domain_decider", provide_context = True)
    def domain_choice(choices, **kwargs):
        ti = kwargs['ti']
        values = ti.xcom_pull(task_ids="read_data", key="data")
        entity_name = values["id"]
        
        for opt in options:
            if re.search(opt, entity_name, re.IGNORECASE):
                return opt
                
        return options[-1]
 

    task1 = domain_choice(choices=options)
    
    join = EmptyOperator(
    	task_id = "join_after_choice",
    	trigger_rule="all_done"
    )
    
    
    
    functions_dict = {
        'pharma': trigger_pharma,
        'sidenor': trigger_steel,
        'idalsa': trigger_aluminium,
        'asphalt': trigger_asphalt
    }
    
    for idx, option in enumerate(options[:-1]):

        t = PythonOperator(
    	    task_id = option,
    	    python_callable = functions_dict[option],
    	    dag = dag,
    	    provide_context = True)
        
        label = labels[idx]
        
        task0 >> task1 >> Label(label) >> t >> join
       
        
    t = EmptyOperator(
        task_id = options[-1]
    )
    
    task0 >> task1 >> Label("Skip") >> t >> join
        
    

    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
