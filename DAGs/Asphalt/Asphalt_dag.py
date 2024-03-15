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



    
    
def check_RPA0700_sensor(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_t_RPBCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_RPA0700_max']["value"]["value"])

    if val1 > 0 and val2 == 0:
        alert = f"1||{['DataIngestion_production_t_RPBCount', 'DataIngestion_production_RPA0700_max']}||Sensor Error||rule broken||{[val1, val2]}||None||None"
        return [alert]
    
    return []
    
    
    
    
def check_ST_Frames(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_t_STCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_t_SPCount']["value"]["value"])

    if val1 == 0 and val2 > 0:
        alert = f"1||{['DataIngestion_production_t_STCount', 'DataIngestion_production_t_SPCount']}||Sensor Error||rule broken||{[val1, val2]}||None||None"
        return [alert]
        
    return []

        
    


def check_RT_Frames(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_t_RTCount']["value"]["value"])
    val2 =  float(values['DataIngestion_production_t_RPBCount']["value"]["value"])

    if val1 == 0 and val2 > 0:
        alert = f"1||{['DataIngestion_production_t_RTCount', 'DataIngestion_production_t_RPBCount']}||Sensor Error||rule broken||{[val1, val2]}||None||None"
        return [alert]
        
    return []
    
    
    
def check_RPA2000_sensor(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA2000_min']["value"]["value"])

    if val1 < 0:
        alert = f"1||DataIngestion_production_RPA2000_min||Sensor Error||lower threshold||{val1}||{0}||None"
        return [alert]
        
    return []



def check_RPA2100_sensor(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA2100_min']["value"]["value"])

    if val1 < 0:
        alert = f"1||DataIngestion_production_RPA2100_min||Sensor Error||lower threshold||{val1}||{0}||{255}"
        return [alert]
    elif val1 > 255:
        alert = f"1||DataIngestion_production_RPA2100_min||Sensor Error||upper threshold||{val1}||{0}||{255}"
        return [alert]
        
    return []

        
        
def check_RPA1000_sensor(**kwargs):
    
    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    val1 =  float(values['DataIngestion_production_RPA1000_min']["value"]["value"])

    if val1 < 0:
        alert = f"1||DataIngestion_production_RPA1000_min||Sensor Error||lower threshold||{val1}||0||None"
        return [alert]
        
    return []
    
   
    


##################################################################################### SOLUTION 2 FUNCTIONS ############################################################################


    
    
    
##################################################################################### SOLUTION 3 FUNCTIONS ############################################################################


    

##################################################################################### SOLUTION 4 FUNCTIONS ############################################################################



def check_DAPA_change(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    alert_list = []
    
    for idx, attr in enumerate(config["solution_4_inputs_1"]):
        try:
            attr_val = float(values[attr]["value"]["value"])
            attr_lower_threshold = config["solution_4_lower_thresholds_1"][idx]
            attr_upper_threshold = config["solution_4_upper_thresholds_1"][idx]
            
            if attr_val < attr_lower_threshold:
                alert_list.append(f"4||{attr}||D. APA Change Error||lower threshold||{attr_val}||{attr_lower_threshold}||{attr_upper_threshold}")
            elif attr_val > attr_upper_threshold:
                alert_list.append(f"4||{attr}||D. APA Change Error||upper threshold||{attr_val}||{attr_lower_threshold}||{attr_upper_threshold}")
                
        except Exception as e:
            print(e)
            alert_list.append(f"4||{attr}||AM Error||AM ERROR occurred with variable||None||None||None")
                
    return alert_list




def check_laboratory_inputs(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    alert_list = []
    
    for idx, attr in enumerate(config["solution_4_inputs_2"]):
        try:
            attr_val = float(values[attr]["value"]["value"])
            attr_upper_threshold = config["solution_4_upper_thresholds_2"][idx]
            
            if attr_val > attr_upper_threshold:
                alert_list.append(f"4||{attr}||Data Input Error||upper threshold||{attr_val}||{attr_lower_threshold}||{attr_upper_threshold}")
                
        except Exception as e:
            print(e)
            alert_list.append(f"4||{attr}||AM Error||AM ERROR occurred with variable||None||None||None")
                
    return alert_list

    


    
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

        print(values.keys())
        
        sol1_keys = config["solution_1_inputs"]
        sol1_dict = {key: values[key] for key in sol1_keys}  
        if len(sol1_dict) == len(sol1_keys) and entity_name == config['small']:
            return choices[0]
        
            
        sol2_keys = [key for key in values.keys() if ("_OCT_signalQualityCheck_maxSignalIntensity" in key) or ("OCT_image" in key)]
        sol2_dict = {key: values[key] for key in sol2_keys}
        if len(sol2_keys) > 0:
            return choices[1]

            
        sol3_keys = [key for key in values.keys() if ("_IR_" in key)]
        sol3_dict = {key: values[key] for key in sol3_keys}
        if len(sol3_keys) > 0:
            return choices[2]
        
        
        sol4_keys = config["solution_4_inputs_1"]
        sol4_keys.extend(config["solution_4_inputs_2"])
        sol4_dict = {key: values[key] for key in sol4_keys}
        if len(sol4_keys) > 0 and entity_name == config['small']:
            return choices[3]


        sol5_keys = [key for key in values.keys() if ("RuntimeAIProcessing" in key)]
        sol5_dict = {key: values[key] for key in sol4_keys}      
        if len(sol5_keys) > 0:
            return choices[4]
        
        
        return choices[-1]
        
    #task_0_1 = decide_solution(choices = solution_options)
    
    
    # Join after solution execution
    join_0 = EmptyOperator(
    	task_id = "join_end_dag",
    	trigger_rule="none_failed"
    )
    
    skip_0 = EmptyOperator(
    	task_id = "skip_all_solutions"
    )
        
    
    ######################### Solution 1 Taksks ################################
    
    task_ids_solution1 = ["check_RPA0700_sensor", "check_ST_Frames", "check_RT_Frames", "check_RPA2000_sensor", "check_RPA2100_sensor", "check_RPA1000_sensor"]
    
    
    task_1_0 = EmptyOperator(
    	task_id = "solution_1",
    )
    
    task_1_2 = PythonOperator(
    	task_id = "execute_alerting_1",
    	python_callable = notify_anomalies,
    	op_kwargs = {"tasks" : task_ids_solution1},
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    
    functions_dict_solution1 = {
        'check_RPA0700_sensor': check_RPA0700_sensor,
        'check_ST_Frames': check_ST_Frames,
        'check_RT_Frames': check_RT_Frames,
        'check_RPA2000_sensor': check_RPA2000_sensor,
        'check_RPA2100_sensor': check_RPA2100_sensor,
        'check_RPA1000_sensor': check_RPA1000_sensor
    }
    
    
    tasks_1 = []
    for tassk in task_ids_solution1:
        
        t_1_1 = PythonOperator(
    	    task_id = tassk,
    	    python_callable = functions_dict_solution1[tassk],
    	    dag = dag,
    	    provide_context = True
        )
        
        tasks_1.append(t_1_1)
        
        
        
    sol_1_options = ["execute_alerting_1", "skip_1"]
    @task.branch(task_id="plan_action_1", provide_context = True, trigger_rule="all_success")
    def plan_action_1(choices, **kwargs):
        ti = kwargs['ti']
        alerts = ti.xcom_pull(task_ids=task_ids_solution1)
        alerts = [item for row in alerts for item in row]
        
        if len(alerts) > 0:
            return choices[0]

        return choices[1]
        
    task_1_3 = plan_action_1(choices=sol_1_options)    
    
    join_1 = EmptyOperator(
    	task_id = "join_for_solution_1",
    	trigger_rule="none_failed"
    )
    
	
    skip_1 = EmptyOperator(
    	task_id = "skip_1",
    )
    
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
    	task_id = "skip_3"
    )
    
    
    ######################### Solution 4 Taksks ################################
    
    task_ids_solution4 = ["check_DAPA_change", "check_laboratory_inputs"]
    
    task_4_0 = EmptyOperator(
    	task_id = "solution_4"
    )
    
    
    task_4_1 = PythonOperator(
    	task_id = "check_DAPA_change",
    	python_callable = check_DAPA_change,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='all_success'
    )
    
    
    task_4_2 = PythonOperator(
    	task_id = "check_laboratory_inputs",
    	python_callable = check_laboratory_inputs,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='all_success'
    )
    
    

    sol_4_options = ["execute_alerting_4", "skip_4"]
    @task.branch(task_id="plan_action_4", provide_context = True, trigger_rule="all_success")
    def plan_action_4(choices, **kwargs):
        ti = kwargs['ti']
        alert_DAPA = ti.xcom_pull(task_ids="check_DAPA_change")
        alert_lab = ti.xcom_pull(task_ids="check_laboratory_inputs")
        
        if len(alert_DAPA) > 0 or len(alert_lab) > 0:
            return choices[0]

        return choices[1]
        
    task_4_3 = plan_action_4(choices=sol_4_options)
    
    
    task_4_4 = PythonOperator(
    	task_id = "execute_alerting_4",
    	python_callable = notify_anomalies,
    	op_kwargs = {"tasks" : ["check_DAPA_change", "check_laboratory_inputs"]},
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    join_4 = EmptyOperator(
    	task_id = "join_for_solution_4",
    	trigger_rule="none_failed"
    )
    
	
    skip_4 = EmptyOperator(
    	task_id = "skip_4"
    )
    
    
    
    
    ############################################################################# TASK ORDERING ############################################################################################
    
    
    
    task_0_0 >> [task_1_0, task_2_0, task_3_0, task_4_0]
    task_0_0 >> skip_0 >> join_0

        
    task_1_0 >> tasks_1 >> task_1_3
    task_1_3 >> task_1_2 >> join_1
    task_1_3 >> skip_1 >> join_1

    
    #task_2_0 >> task_2_4 >> task_2_3 >> task_2_1 >> join_2
    #task_2_0 >> task_2_4>> task_2_3 >> task_2_2 >> join_2
    #task_2_0 >> task_2_4 >> task_2_3 >> skip_2 >> join_2
    task_2_0 >> skip_2 >> join_2
    
    #task_3_0 >> task_3_3 >> task_3_2 >> task_3_1 >> join_3
    #task_3_0 >> task_3_3 >> task_3_2 >> skip_3 >> join_3
    task_3_0 >> skip_3 >> join_3

    task_4_0 >> [task_4_1 , task_4_2] >> task_4_3
    task_4_3 >> skip_4 >> join_4
    task_4_3 >> task_4_4 >> join_4
    
    
    join_1 >> join_0
    join_2 >> join_0
    join_3 >> join_0
    join_4 >> join_0
    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
