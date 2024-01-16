import requests
import json
from datetime import datetime

def update_position_status(pos_x, pos_y): 
    url = "http://136.243.156.113:1026/ngsi-ld/v1/entities/urn:ngsi-ld:Pharma_smaller_time_window:001/attrs"
    body = json.loads('''
    {
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "DataIngestion_OCT_probePosition_yPos": {
        "type": "Property",
        "value": {
            "value": y,
            "dateObserved": "24-01-03T15:28:17Z",
            "timeWindowLengthMinutes": "5"
        }
    },
    "DataIngestion_OCT_probePosition_xPos": {
        "type": "Property",
        "value": {
            "value": x,
            "dateObserved": "24-01-03T15:28:17Z",
            "timeWindowLengthMinutes": "5"
        }
    }
    }
    ''')
    
    headers = {"Content-Type": "application/ld+json" }
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    body["DataIngestion_OCT_probePosition_yPos"]["value"]["dateObserved"] = now
    body["DataIngestion_OCT_probePosition_xPos"]["value"]["dateObserved"] = now
    
    body["DataIngestion_OCT_probePosition_yPos"]["value"]["value"] = pos_y
    body["DataIngestion_OCT_probePosition_xPos"]["value"]["value"] = pos_x
    r = requests.patch(url, headers=headers, data=json.dumps(body))
    print(r.status_code, r.text)
  
    
