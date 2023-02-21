from flask import render_template
import sys
from app import create_app
from IxOSRest import start_chassis_rest_data_fetch


app = create_app()

CHASSIS_LIST = [
{
    "ip": "10.36.236.121",
    "username": "admin",
    "password": "Kimchi123Kimchi123!",
    "os": "linux",
    "fetch": ""
},
{
    "ip": "10.36.236.121",
    "username": "admin",
    "password": "Kimchi123Kimchi123!",
    "os": "linux",
    "fetch": ""
}
]

@app.get("/")
def home():
    list_of_chassis_information = []
    for idx, chassis in enumerate(CHASSIS_LIST):
        complete_chassis_repsonse = start_chassis_rest_data_fetch(chassis["ip"], chassis["username"], chassis["password"])
        
        complete_chassis_repsonse["chassis_information"].update({"chassisName": f"Chassis{idx+1}"})
        if "XGS12" in complete_chassis_repsonse["chassis_information"]["type"]:
            complete_chassis_repsonse["chassis_information"].update({"chassis_model_img_src": "https://cdn.cs.1worldsync.com/50/53/5053b84f-311b-4f29-bf7e-2d451293a688.jpg"})
        
        
        list_of_chassis_information.append(complete_chassis_repsonse)

    return render_template("index.html", data=list_of_chassis_information)
