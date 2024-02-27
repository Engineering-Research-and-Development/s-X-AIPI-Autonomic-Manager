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

f = open("/opt/airflow/dags/configs/steel.json", "r")
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


def check_scrap_zeros(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    zero_list = []
    
    for scrap in config["solution_1_zeros_inputs"]:
        try:
            scrap_val = values[scrap]["value"]["value"]
            if scrap_val > 0:
                zero_list.append("Zero values detected in parameter: " +scrap)
        except Exception as e:
            print(e)
            zero_list.append("AM ERROR occurred with variable " + scrap )
                
    return zero_list
    
    
def check_scrap_nans(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    zero_list = []
    
    for scrap in config["solution_1_nan_inputs"]:
        try:
            scrap_val = values[scrap]["value"]["value"]
            if scrap_val > 0:
                zero_list.append("Missing values detected in parameter: " +scrap)
        except Exception as e:
            zero_list.append("AM ERROR occurred with variable " + scrap )
            print(e)
                
    return zero_list
     
    
    
def notify_anomalies_1(**kwargs):

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
    
    l = []
    for lists in values:
        l.extend(lists)
    
    for alert in l:
        text = "Solution 1 generated the following alert: " + alert
        body["AM_Generated_Alarm"]["value"]["value"] = text
        body["AM_Generated_Alarm"]["value"]["dateUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.patch(config['AM_Alert_Output_1'], headers=headers, data=json.dumps(body))
        print(r.status_code, r.text)
        
         
        
        
def raise_transformation_alert(**kwargs):

    values = kwargs['data']
    
    values = values.split("'")
    values = [val for val in values if len(val) > 10]
    

    for elem in values:
        elem = "Solution 1 generated the following alert: " + elem
        yield(json.dumps(0), json.dumps(elem))
    



def get_scrap_params(attr):

    name = get_scrap_name(attr)
    param_name_1 = name + "_periods"
    param_name_2 = name + "_status"
    param_name_3 = name + "_previous"
    
    return param_name_1, param_name_2, param_name_3
    
    
    

def get_scrap_name(attr):
    
    #first = attr.split("scrap_")[-1]
    #name = first.split("_zero")[0]
    name = attr.split("_zero")[0]
    
    return name



def write_if_not_exist(attr, ent):

    param_name_1, param_name_2, param_name_3 = get_scrap_params(attr)
    
    
    keys = list(ent.keys())
    if param_name_1 in keys : return
    
    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    body = {}
    body['@context'] = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
    
    # Periods of observations
    body[param_name_1] = {}
    body[param_name_1]["type"] = "Property"
    body[param_name_1]["value"] = {}
    body[param_name_1]["value"]["value"] = 0
    body[param_name_1]["value"]["dateUpdated"] = now
    
    # Previous status: check conditions, if in treshold then it is used, otherwise not used
    body[param_name_3] = {}
    body[param_name_3]["type"] = "Property"
    body[param_name_3]["value"] = {}
    body[param_name_3]["value"]["value"] = "Not Used"
    body[param_name_3]["value"]["dateUpdated"] = now
    
    # Confirmed status: here the answer from HITL
    body[param_name_2] = {}
    body[param_name_2]["type"] = "Property"
    body[param_name_2]["value"] = {}
    body[param_name_2]["value"]["value"] = "Not Used"
    body[param_name_2]["value"]["dateUpdated"] = now
    
    url = config["AM_HITL_Status_1"]
    
    r = requests.post(url, headers=headers, data=json.dumps(body))
    print(r.status_code, r.text)
    return
    


    
def analyze_materials_used(**kwargs):


    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    

    max_0 = config["solution_1_scrapmax_inputs_0"]
    max_1 = config["solution_1_scrapmax_inputs_1"]
    max_2 = config["solution_1_scrapmax_inputs_2"]
    max_3 = config["solution_1_scrapmax_inputs_3"]

    
    zeros = []
    zero_0 = config["solution_1_scrapzeros_inputs_0"]
    zero_1 = config["solution_1_scrapzeros_inputs_1"]
    zero_2 = config["solution_1_scrapzeros_inputs_2"]
    zero_3 = config["solution_1_scrapzeros_inputs_3"]
    zeros.extend(zero_0)
    zeros.extend(zero_1)
    zeros.extend(zero_2)
    zeros.extend(zero_3)
    
    nrheats = []
    heat_1 = list(config["solution_1_nrheats_scrap"])
    heat_2 = list(config["solution_1_nrheats_limecoke"])
    
    
    entity = requests.get(config["AM_HITL_Status_1_GET"]).json()
    print(entity)
    
    for scrap in zeros:
        write_if_not_exist(scrap, entity)
        
    entity = requests.get(config["AM_HITL_Status_1_GET"]).json()
    
    ti.xcom_push(key="prev_status", value=entity)



# TODO Make a separate step
def status_update(param_name_3, prev, param_name_1, periods, **kwargs):


    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    body = {}
    body['@context'] = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
    
    body[param_name_1] = {}
    body[param_name_1]["type"] = "Property"
    body[param_name_1]["value"] = {}
    body[param_name_1]["value"]["value"] = periods
    body[param_name_1]["value"]["dateUpdated"] = now
    
    body[param_name_3] = {}
    body[param_name_3]["type"] = "Property"
    body[param_name_3]["value"] = {}
    body[param_name_3]["value"]["value"] = prev
    body[param_name_3]["value"]["dateUpdated"] = now
    
    url = config["AM_HITL_Status_1"]
    
    r = requests.post(url, headers=headers, data=json.dumps(body))
    print(r.status_code, r.text)
    return

    


def check_materials(**kwargs):

    ti = kwargs['ti']
    
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    entity = ti.xcom_pull(task_ids="analyze_materials_used", key="prev_status")
    zeros = kwargs['zeros']
    maxes = kwargs['maxes']
    reference = kwargs['reference']
    message = kwargs['error_message_start']
       

    for idx, attr in enumerate(zeros):
    
        # Current zero
        zero = int(values[attr]["value"]["value"])
        
        # Current Max
        max_attr = maxes[idx]
        mx = int(values[max_attr]["value"]["value"])
        
        # Current Reference
        nr_heats = int(values[reference]["value"]["value"])
        
        # Get parameter names for previous state
        param_name_1, param_name_2, param_name_3 = get_scrap_params(attr)
        name = get_scrap_name(attr)
    
    	# Getting previous status info
        periods = int(entity[param_name_1]["value"]["value"])
        was_used = entity[param_name_2]["value"]["value"]
        previous_status = entity[param_name_3]["value"]["value"]
        
        # First: check if scrap is used (#max > 0 & #zeros < #heats). 
        is_used = "Not Used"
        if mx > 0 and zero < nr_heats: is_used = "Used"
        
        # Check previous status if is the same of current
        # If is the same, add +1 to periods, otherwise set them to 1
        if is_used == previous_status: 
            periods += 1
        else:
            periods = 1
        
        status_update(param_name_3, is_used, param_name_1, periods, **kwargs)
        
        # If current periods out is > 2, check HITL status
        # If HITL status different, send alert
        if periods > 2 and is_used != was_used:
            if "Not" in was_used:
                return message + "was introduced. Please, send confirmation. Parameter triggering alert: " + name + " for " + str(periods) + " time windows."
            else:
                return message + "was removed. Please, send confirmation. Parameter triggering alert: " + name + " for " + str(periods) + " time windows."
    
    
    
    


##################################################################################### SOLUTION 2 FUNCTIONS ############################################################################


    
    
    
##################################################################################### SOLUTION 3 FUNCTIONS ############################################################################


    

##################################################################################### SOLUTION 4 FUNCTIONS ############################################################################



    
############################################################################### DAG & TASK DEFINITION ################################################################################################

with DAG(
	dag_id = 'steel_dag',
	description = "Steel Dag",
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
    
    task_ids_solution1 = ["analyze_scrap_zeros", "analyze_scrap_nans", "analyze_first_group", "analyze_second_group", "analyze_third_group", "analyze_fourth_group"]
    
    
    task_1_1 = PythonOperator(
    	task_id = "analyze_scrap_zeros",
    	python_callable = check_scrap_zeros,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    task_1_2 = PythonOperator(
    	task_id = "analyze_scrap_nans",
    	python_callable = check_scrap_nans,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    task_1_3 = EmptyOperator(
        task_id = "end_analysis",
        trigger_rule='none_failed'
    )
    
    task_1_4 = PythonOperator(
    	task_id = "notify_anomalies_1",
    	python_callable = notify_anomalies_1,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    
    task_1_5 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="raise_transformation_alert",
        topic="steel-alerts",
        producer_function=raise_transformation_alert,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids=['analyze_scrap_zeros', 'analyze_scrap_nans', 'analyze_first_group', 'analyze_second_group', 'analyze_third_group', 'analyze_fourth_group'])}}"
        },
        poll_timeout=10
    )
    
     
    task_1_6 = PythonOperator(
    	task_id = "analyze_materials_used",
    	python_callable = analyze_materials_used,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    
    task_1_7 = PythonOperator(
    	task_id = "analyze_first_group",
    	python_callable = check_materials,
    	dag = dag,
    	provide_context = True,
    	op_kwargs={'error_message_start': 'First group of scraps ', 'maxes': config["solution_1_scrapmax_inputs_0"], 
    	    "zeros": config["solution_1_scrapzeros_inputs_0"], "reference": config["solution_1_nrheats_scrap"]},
    	trigger_rule='none_failed'
    )
     
    task_1_8 = PythonOperator(
    	task_id = "analyze_second_group",
    	python_callable = check_materials,
    	dag = dag,
    	provide_context = True,
    	op_kwargs={'error_message_start': 'Second group of scraps ', 'maxes': config["solution_1_scrapmax_inputs_1"], 
    	    "zeros": config["solution_1_scrapzeros_inputs_1"], "reference": config["solution_1_nrheats_scrap"]},
    	trigger_rule='none_failed'
    )
    
    task_1_9 = PythonOperator(
    	task_id = "analyze_third_group",
    	python_callable = check_materials,
    	dag = dag,
    	provide_context = True,
    	op_kwargs={'error_message_start': 'Lime basket content ', 'maxes': config["solution_1_scrapmax_inputs_2"], 
    	    "zeros": config["solution_1_scrapzeros_inputs_2"], "reference": config["solution_1_nrheats_lime"]},
    	trigger_rule='none_failed'
    )
    
    
    task_1_10 = PythonOperator(
    	task_id = "analyze_fourth_group",
    	python_callable = check_materials,
    	dag = dag,
    	provide_context = True,
    	op_kwargs={'error_message_start': 'Lime coke content ', 'maxes': config["solution_1_scrapmax_inputs_3"], 
    	    "zeros": config["solution_1_scrapzeros_inputs_3"], "reference": config["solution_1_nrheats_limecoke"]},
    	trigger_rule='none_failed'
    )


        
    
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
    
    
    
    task_0_0 >> [task_1_0, task_2_0, task_3_0, task_4_0]



        
    task_1_0 >> [task_1_1, task_1_2] >> task_1_3 >> [task_1_4, task_1_5] >> join_1
    task_1_0 >> task_1_6 >> [task_1_7, task_1_8, task_1_9, task_1_10] >> task_1_3 >> [task_1_4, task_1_5] >> join_1
     
    #task_2_0 >> task_2_4 >> task_2_3 >> task_2_1 >> join_2
    #task_2_0 >> task_2_4>> task_2_3 >> task_2_2 >> join_2
    #task_2_0 >> task_2_4 >> task_2_3 >> skip_2 >> join_2
    
    #task_3_0 >> task_3_3 >> task_3_2 >> task_3_1 >> join_3
    #task_3_0 >> task_3_3 >> task_3_2 >> skip_3 >> join_3
    
    #task_4_0 >> task_4_3 >> task_4_2 >> task_4_1 >> join_4
    #task_4_0 >> task_4_3 >> task_4_2 >> skip_4 >> join_4
    task_4_0 >> skip_4 >> join_4
    
    join_1 >> join_0
    #join_2 >> join_0
    #join_3 >> join_0
    join_4 >> join_0
    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
