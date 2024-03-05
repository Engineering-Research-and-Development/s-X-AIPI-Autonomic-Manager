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
    

    

def raise_transformation_alert(**kwargs):

    values = kwargs['data']
    
    values = values.split("'")
    values = [val for val in values if len(val) > 10]
    

    for elem in values:
        params = elem.split("||")
        body = {}
        body["Solution"] = params[0]
        body["Parameter"] = params[1]
        body["AlertType"] = params[2]
        body["AlertDescription"] = params[3]
        body["AlertTimestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        yield(json.dumps(0), json.dumps(body))




def add_param_to_body(body, param_name, param_value, now):

    if param_value is not None:
        body[param_name] = {}
        body[param_name]["type"] = "Property"
        body[param_name]["value"] = {}
        body[param_name]["value"]["value"] = param_value
        body[param_name]["value"]["dateUpdated"] = now
    
    return body
    


# TODO Make a separate step
def update_HITL_entity(names, values, url):

    
    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    body = {}
    body['@context'] = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
    
    for idx, name in enumerate(names):
        body = add_param_to_body(body, name, values[idx], now)


    r = requests.post(url, headers=headers, data=json.dumps(body))
    print(r.status_code, r.text)
    return




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
        if type(lists) == type(["test"]):
            l.extend(lists)
        elif type(lists) == type("string"):
            l.append(lists)
    
    for alert in l:
        body["AM_Generated_Alarm"]["value"]["value"] = alert.replace("||", " ")
        body["AM_Generated_Alarm"]["value"]["dateUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.patch(config['AM_Alert_Output_1'], headers=headers, data=json.dumps(body))
        print(r.status_code, r.text)
    return
    
    
##################################################################################### SOLUTION 1 FUNCTIONS ############################################################################


def check_scrap_zeros(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    zero_list = []
    
    for scrap in config["solution_1_zeros_inputs"]:
        try:
            scrap_val = values[scrap]["value"]["value"]
            if scrap_val > 0:
                zero_list.append(f"Solution 1||{scrap}||Zero Detected||{scrap_val} zero values detected in {scrap}")
        except Exception as e:
            print(e)
            zero_list.append(f"Solution 1||{scrap}||AM Error||AM ERROR occurred with variable {scrap}")
                
    return zero_list
    
    
def check_scrap_nans(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    zero_list = []
    
    for scrap in config["solution_1_nan_inputs"]:
        try:
            scrap_val = values[scrap]["value"]["value"]
            if scrap_val > 0:
                zero_list.append(f"Solution 1||{scrap}||Missing Values||{scrap_val} NaN values detected in {scrap}")
        except Exception as e:
            zero_list.append(f"Solution 1||{scrap}||AM Error||AM ERROR occurred with variable {scrap}")
            print(e)
                
    return zero_list
     
    


def get_scrap_params(attr):

    name = get_scrap_name(attr)
    param_name_1 = name + "_periods"
    param_name_2 = name + "_status"
    param_name_3 = name + "_previous"
    param_name_4 = name + "_confirmed"
    
    return param_name_1, param_name_2, param_name_3, param_name_4
    
    
    

def get_scrap_name(attr):
    
    #first = attr.split("scrap_")[-1]
    #name = first.split("_zero")[0]
    name = attr.split("_zero")[0]
    
    return name



def write_if_not_exist(attr, ent):

    param_name_1, param_name_2, param_name_3, param_name_4 = get_scrap_params(attr)
    
    keys = list(ent.keys())
    if param_name_1 in keys : return
    
    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    
    status_update(attr, 1, "Not Used", "Not Used", "No")
    
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
def status_update(attr, periods, status, is_used, confirmed, **kwargs):

    param_name_1, param_name_2, param_name_3, param_name_4 = get_scrap_params(attr)
    names = [param_name_1, param_name_2, param_name_3, param_name_4]
    values = [periods, status, is_used, confirmed]
    
    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    body = {}
    body['@context'] = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
    
    for idx, name in enumerate(names):
        body = add_param_to_body(body, name, values[idx], now)

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
        param_name_1, param_name_2, param_name_3, param_name_4 = get_scrap_params(attr)
        name = get_scrap_name(attr)
    
    	# Getting previous status info
        periods = int(entity[param_name_1]["value"]["value"])
        status = entity[param_name_2]["value"]["value"]
        previous_status = entity[param_name_3]["value"]["value"]
        confirmed = entity[param_name_4]["value"]["value"]
        
        # First: check if scrap is used (#max > 0 & #zeros < #heats). 
        is_used = "Not Used"
        if mx > 0 and zero < nr_heats: is_used = "Used"
        
        # Check previous status if is the same of current
        # If is the same, add +1 to periods, otherwise set them to 1
        if is_used == previous_status: 
            periods += 1
        else:
            periods = 1
        

        status_update(attr, periods, None, is_used, None)
        
        # If current periods out is > 2, check HITL status
        # If HITL status different, send alert
        if periods > 2 and is_used != status and "No" in confirmed:
            if "Not" in status:
                return f"Solution 1||{name}||Material Introduction Detection||{message} was introduced: {name} changed values for {periods} time windows. Please send confirmation to autonomic manager"
            else:
                return f"Solution 1||{name}||Material Removal Detection||{message} was introduced: {name} changed values for {periods} time windows. Please, send confirmation to autonomic manager"
    
    
    
    


##################################################################################### SOLUTION 2 FUNCTIONS ############################################################################



def update_sol2_HITL(name, value, name_2, value_2):

    
    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    body = {}
    body['@context'] = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
    
    body = add_param_to_body(body, name, value, now)
    body = add_param_to_body(body, name_2, value_2, now)

    url = config["AM_HITL_Status_2"]
    
    r = requests.post(url, headers=headers, data=json.dumps(body))
    print(r.status_code, r.text)
    return
    



def analyze_sol2_anomalies(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
    conf_standards = ["Unconfirmed", "Confirmed_Anomalies", "Confirmed_Normal"]
    alert_standards = ["NoAlert", "Alert"]
    
       
    alert_list = []
    
    inputs = config["solution_2_inputs"]
    thresholds = config["solution_2_thresholds"]
    
    entity = requests.get(config["AM_HITL_Status_2_GET"]).json()
    keys = list(entity.keys())
    print(entity)
    
    hitl_url = config["AM_HITL_Status_2"] 
    
    # Add OCB entry if not exist yet
    for attr in inputs:
        name = attr + "_HITL_anomalies_confirmation"
        name_2 = attr + "_previous_status"
        if name_2 in keys: continue
        update_HITL_entity([name, name_2], [conf_standards[0], alert_standards[0]], hitl_url)
        #update_sol2_HITL(name, conf_standards[0], name_2, alert_standards[0])    
        
    
        
    # Check value. Send alert if current status is not confirmed and breaks tresh   
    entity = requests.get(config["AM_HITL_Status_2_GET"]).json() 
    for idx, var in enumerate(inputs):
        name = var + "_HITL_anomalies_confirmation"
        name_2 = var + "_previous_status"
        try:
            var_val = values[var]["value"]["value"]
            confirmation = entity[name]["value"]["value"]
            old_val = entity[name_2]["value"]["value"]
            
            cur_val = alert_standards[0]
            
            if var_val > thresholds[idx]:
                cur_val = alert_standards[1]
                
                
            if cur_val != old_val:
                update_HITL_entity([name, name_2], [conf_standards[0], cur_val], hitl_url)
                #update_sol2_HITL(name, conf_standards[0], name_2, cur_val)
                confirmation = conf_standards[0]
            
            if cur_val == alert_standards[1] and confirmation == conf_standards[0]:
                alert_list.append(f"Solution 2||{var}||Anomaly Detected||Parameter {var} is out of bound with value {var_val}. Please confirm or deny anomaly to the autonomic manager.")
            elif cur_val == alert_standards[1] and confirmation == conf_standards[1]:
                alert_list.append(f"Solution 2||{var}||Anomaly Persistence||Parameter {var} is confirmed as anomaly with {var_val}. Requested HITL intervention.")
                
            
            
        except Exception as e:
            print("Exception was:", e)
            alert_list.append(f"Solution 2||{var}||AM Error||AM ERROR occurred with variable {var}")
            
        
        
                
    return alert_list
    
    
    

    
##################################################################################### SOLUTION 3 FUNCTIONS ############################################################################



def check_model_accuracy(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    

    inputs = config["solution_3_inputs"]
    tresholds = config["solution_3_thresholds"]
    
  
    alert_list = []
        
    # Check value. Send alert if current status is not confirmed and breaks treshikd    
    for idx, var in enumerate(inputs):
        try:
            var_val = values[var]["value"]["value"]
            tresh = tresholds[idx]
            var_tresh = values[tresh]["value"]["value"]
            
            if var_val > var_tresh*1.15:
                alert_list.append(f"Solution 3||{var}||Model Accuracy Decreased||{var} is {var_val*100/var_tresh}% higher than {tresh}")

        except Exception as e:
            print("Exception was:", e)
            alert_list.append(f"Solution 3||{var}||AM Error||AM ERROR occurred with variable {var}")
            
        
        
                
    return alert_list
    

##################################################################################### SOLUTION 4 FUNCTIONS ############################################################################


def analyze_coefficients_anomalies(**kwargs):

    ti = kwargs['ti']
    values = ti.xcom_pull(task_ids="monitor_data", key="data")
    
      
    alert_list = []
    
    inputs = config["solution_4_inputs"]
    hitl_names = [inp+"_previous_value" for inp in inputs]
    
    entity = requests.get(config["AM_HITL_Status_4_GET"]).json()
    keys = list(entity.keys())
    print(entity)
    
    hitl_url = config["AM_HITL_Status_4"] 
    
    # Add OCB entry if not exist yet
    for idx, var in enumerate(inputs):
        name = hitl_names[idx]
        if name in keys: continue
        cur_val = values[var]["value"]["value"]
        update_HITL_entity([name], [cur_val], hitl_url)
        
        
    entity = requests.get(config["AM_HITL_Status_4_GET"]).json()
        
    # Check value. Send alert if current status is not confirmed and breaks tresh    
    for idx, var in enumerate(inputs):
        name = name = hitl_names[idx]
        
        
        try:
            old_val = entity[name]["value"]["value"]
            cur_val = values[var]["value"]["value"]
            
            low_thresh = old_val - 0.15*np.abs(old_val)
            high_thresh = old_val + 0.15*np.abs(old_val)
            
            if cur_val < low_thresh or cur_val > high_thresh:
                alert_list.append(f"Solution 4||{var}||Copper Content Changed||Parameter {var} is out of bounds with value {cur_val} against lower threshold {low_thresh} \
                and high threshold {low_thresh}. Please update the scrap copper content in database for scrap mix optimizer.")
        
            update_HITL_entity([name], [cur_val], hitl_url)
            
        except Exception as e:
            print("Exception was:", e)
            alert_list.append(f"Solution 4||{var}||AM Error||AM ERROR occurred with variable {var}")
            
        
        
                
    return alert_list


    
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
        task_id = "plan_action_1",
        trigger_rule='none_failed'
    )
    
    task_1_4 = PythonOperator(
    	task_id = "update_am_alert_1",
    	python_callable = notify_anomalies,
    	op_kwargs = {"tasks" : task_ids_solution1},
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    
    task_1_5 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="raise_transformation_alert_1",
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
    
	
    
    
    
    ######################### Solution 2 Taksks ################################
	
    
    task_2_0 = EmptyOperator(
    	task_id = "solution_2",
    )
    
    
    task_2_1 = PythonOperator(
    	task_id = "analyze_sol2_anomalies",
    	python_callable = analyze_sol2_anomalies,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    
    task_2_2 = EmptyOperator(
    	task_id = "plan_action_2",
    	trigger_rule='none_failed'
    )
    
    
    
    task_2_3 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="raise_exploration_alert",
        topic="steel-alerts",
        producer_function=raise_transformation_alert,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids=['analyze_sol2_anomalies'])}}"
        },
        poll_timeout=10
    )
      
    
    join_2 = EmptyOperator(
    	task_id = "join_for_solution_2",
    	trigger_rule="none_failed"
    )
    

    
    
    ######################### Solution 3 Taksks ################################
    
    task_3_0 = EmptyOperator(
    	task_id = "solution_3",
    )
    
    
    task_3_1 = PythonOperator(
    	task_id = "check_model_accuracy",
    	python_callable = check_model_accuracy,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    
    task_3_2 = EmptyOperator(
    	task_id = "plan_action_3",
    	trigger_rule='none_failed'
    )
    
    
    
    task_3_3 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="raise_modeling_alert",
        topic="steel-alerts",
        producer_function=raise_transformation_alert,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids=['check_model_accuracy'])}}"
        },
        poll_timeout=10
    )
     
    
    
    join_3 = EmptyOperator(
    	task_id = "join_for_solution_3",
    	trigger_rule="none_failed"
    )
    

    
    ######################### Solution 4 Taksks ################################
    
    task_4_0 = EmptyOperator(
    	task_id = "solution_4",
    )
    
    
    task_4_1 = PythonOperator(
    	task_id = "analyze_coefficients_anomalies",
    	python_callable = analyze_coefficients_anomalies,
    	dag = dag,
    	provide_context = True,
    	trigger_rule='none_failed'
    )
    
    
    task_4_2 = EmptyOperator(
    	task_id = "plan_action_4",
    	trigger_rule='none_failed'
    )
    
    
    
    task_4_3 = ProduceToTopicOperator(
        kafka_config_id="kafka_broker",
        task_id="raise_copper_content_alert",
        topic="steel-alerts",
        producer_function=raise_transformation_alert,
        producer_function_kwargs={
            "data": "{{ti.xcom_pull(task_ids=['analyze_coefficients_anomalies'])}}"
        },
        poll_timeout=10
    )
    
    
    
    join_4 = EmptyOperator(
    	task_id = "join_for_solution_4",
    	trigger_rule="none_failed"
    )
    

    
    
    
    
    ############################################################################# TASK ORDERING ############################################################################################
    
    
    
    task_0_0 >> [task_1_0, task_2_0, task_3_0, task_4_0, skip_0]

        
    task_1_0 >> [task_1_1, task_1_2] >> task_1_3 >> [task_1_4, task_1_5] >> join_1
    task_1_0 >> task_1_6 >> [task_1_7, task_1_8, task_1_9, task_1_10] >> task_1_3 >> [task_1_4, task_1_5] >> join_1
     
    task_2_0 >> task_2_1 >> task_2_2 >> task_2_3 >> join_2
    
    task_3_0 >> task_3_1 >> task_3_2 >> task_3_3 >> join_3

    task_4_0 >> task_4_1 >> task_4_2 >> task_4_3 >> join_4
    
    
    join_1 >> join_0
    join_2 >> join_0
    join_3 >> join_0
    join_4 >> join_0
    skip_0 >> join_0
    
    
  
    
    
    
   

    
    
    
    
    
    
    
    
