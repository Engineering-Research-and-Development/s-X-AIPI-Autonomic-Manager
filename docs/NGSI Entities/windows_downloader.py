import requests
from datetime import date
import os
from yaml import safe_load
import json

if __name__ == "__main__":

    today = date.today()
    day = today.day
    month = today.month
    year = today.year

    folder_name = f"{day}-{month}-{year}"
    if not os.path.isdir(folder_name):
        print(folder_name)
        os.makedirs(folder_name)

    base_url = "http://136.243.156.113:1026/ngsi-ld/v1/entities/"

    with open("config.yml", "r") as c:
        config = safe_load(c)

    for key, item in config.items():
        path = os.path.join(folder_name, key)
        if not os.path.isdir(path):
            os.makedirs(path)

        for itemkey, val in item.items():
            url = base_url+val
            r = requests.get(url)
            fpath = os.path.join(path, itemkey)
            with open(fpath+".json", "w") as f:
                f.write(json.dumps(r.json()))
