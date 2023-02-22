from flask import render_template
import sys
from app import create_app
from IxOSRest import start_chassis_rest_data_fetch
from config import CHASSIS_LIST


app = create_app()

@app.get("/")
def home():
    list_of_chassis_information = []
    img_link = ""
    for idx, chassis in enumerate(CHASSIS_LIST):
        complete_chassis_repsonse = start_chassis_rest_data_fetch(chassis["ip"], chassis["username"], chassis["password"])
        
        complete_chassis_repsonse["chassis_information"].update({"chassisName": f"Chassis{idx+1}"})
        if "XGS12" in complete_chassis_repsonse["chassis_information"]["type"]:
            img_link = "https://cdn.cs.1worldsync.com/50/53/5053b84f-311b-4f29-bf7e-2d451293a688.jpg"
        elif "Ixia PerfectStorm One" in complete_chassis_repsonse["chassis_information"]["type"]:
            img_link = "https://keysight-h.assetsadobe.com/is/image/content/dam/keysight/en/img/prd/network-test/ixia/network-test-hardware/perfectstorm-one1/Allmodels_right_PerfectStormONE-40G_870-0128_L20-550x550.png"
        elif "XGS2" in complete_chassis_repsonse["chassis_information"]["type"]:
            img_link = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRduxtkTM6vPYDHhwlUUse8Np4_Zd5xTeuJNa_G9wJyUw&s"
        elif "Ixia Virtual Test Appliance" in complete_chassis_repsonse["chassis_information"]["type"]:
            img_link = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTJEZ8qzIPaSZbld6HkjbcGXg9Eb51DT5HN7aRZVQzPn2Myo93Onq7PXtWMglYnTnMqy3c&usqp=CAU"
        elif "AresONE" in complete_chassis_repsonse["chassis_information"]["type"]:
            img_link = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsSpRIJSWrDlzpzaNg9URqT3IOfqZPAGrdNOWA0w0MpeVhpU1E9-nhws6GgYdr53Gcmc4&usqp=CAU"
        elif "Novus" in complete_chassis_repsonse["chassis_information"]["type"]:
            img_link = "https://www.keysight.com/content/dam/keysight/en/img/prd/network-test/ixia/network-test-hardware/novus-one-plus-3-5-speed-l2-7-fixed-chassis/NovusOneRight-700px.png?"
            
        
        complete_chassis_repsonse["chassis_information"].update({"chassis_model_img_src": img_link})
        list_of_chassis_information.append(complete_chassis_repsonse)

    return render_template("index.html", data=list_of_chassis_information)
