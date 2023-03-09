from flask import render_template, request, jsonify, redirect
from app import create_app
from IxOSRest_charter import start_chassis_rest_data_fetch as scrdf
from  RestApi.IxOSRestInterface import IxRestSession
from werkzeug.utils import secure_filename
from sqlite3_utilities import read_data_from_database, write_data_to_database, getTagsFromCurrentDatabase, writeTags
from init_db import main


app = create_app()


@app.post("/getLogs")
def getlogs():
    from config import CHASSIS_LIST
    input_json = request.get_json(force=True) 
    chassis_ip = input_json['ip']
    for chassis_item in CHASSIS_LIST:
        if chassis_item["ip"] == chassis_ip:
            chassis = chassis_item
            break
    session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"])
    out = session.collect_chassis_logs(session)
    return jsonify({"resultUrl" : out, "message": "Please login to your chassis and enter this url in browser to download logs"})


@app.get('/')
def upload_file():
    try:
        from config import CHASSIS_LIST
        return redirect("/chassisDetails/fromDBPoll", code=302)
    except Exception:
        return render_template('upload.html')
    
    
@app.get('/upload_file_after_first_load')
def upload_file_after_first_load():
    return render_template('upload.html')
    
	
@app.post('/uploader')
def uploader():
   if request.method == 'POST':
      f = request.files['file']
      f.save(secure_filename(f.filename))
      return redirect("/getBaseData")
  
@app.get('/getBaseData')
def getBaseData():
    load_base_data()
    return redirect("chassisDetails/fromDBPoll", code=302)
  
@app.post('/goDirectToHome')
def goDirectToHome():
    return redirect("/chassisDetails/fromDBPoll", code=302)

@app.get("/chassisDetails", defaults={'refreshState': "freshPoll"})
@app.get("/chassisDetails/<refreshState>")
def chassisDetails(refreshState):
    headers = ["IP","type","chassisSN","controllerSN", "# PhysicalCards", 
               "IxOS", "IxNetwork Protocols", "IxOS REST",
               "MemoryUsed", "TotalMemory", "%CPU Utilization", "Tags"]

    try:
        from config import CHASSIS_LIST
    except Exception:
        # This will create the blank tables for you the first time you load the application
        CHASSIS_LIST = []
    
    list_of_chassis = [] 
    ip_tags_dict = getTagsFromCurrentDatabase(type_of_update="chassis")
    
    if refreshState == "freshPoll" or refreshState == "initData": 

        if CHASSIS_LIST:  
            for chassis in CHASSIS_LIST:
                out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="chassisSummary")
                list_of_chassis.append(out)
            
            write_data_to_database(table_name="chassis_summary_records", records=list_of_chassis, ip_tags_dict=ip_tags_dict)
            
    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="chassis_summary_records")
        for record in records:
            a = {"chassisIp": record["ip"], 
                 "chassisSerial#": record["chassisSN"],
                 "controllerSerial#":record["controllerSN"],
                 "chassisType": record["type_of_chassis"],
                 "physicalCards#": record["physicalCards"],
                 "chassisStatus": record["status_status"],
                 "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"],
                 "IxOS": record["ixOS"],
                 "IxNetwork Protocols": record["ixNetwork_Protocols"],
                 "IxOS REST": record["ixOS_REST"], 
                 "tags": record["tags"].split(","),
                 "mem_bytes": record["mem_bytes"], 
                 "mem_bytes_total": record["mem_bytes_total"],
                 "cpu_pert_usage": record["cpu_pert_usage"],
                 "os": record["os"]}
            list_of_chassis.append(a)
    if refreshState == "initData":
        return "records written"
    return render_template("chassisDetails.html", headers=headers, rows = list_of_chassis, ip_tags_dict=ip_tags_dict)



    
@app.get("/cardDetails", defaults={'refreshState': "freshPoll"})
@app.get("/cardDetails/<refreshState>")
def cardDetails(refreshState):
    headers = ["chassisIP", "ChassisType", "cardNumber", "serialNumber", "cardType", "numberOfPorts"]
    list_of_cards= []
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    
    ip_tags_dict = getTagsFromCurrentDatabase(type_of_update="card")
    if refreshState == "freshPoll" or refreshState == "initData": 
        for chassis in CHASSIS_LIST:
            out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="cardDetails")
            list_of_cards.append(out)
        write_data_to_database(table_name="cards_details_records", records=list_of_cards)

    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="cards_details_records")
        for record in records:
            a = [{"chassisIp": record["chassisIp"], 
                  "chassisType": record["typeOfChassis"],
                  "cardNumber": record["cardNumber"],
                  "serialNumber": record["serialNumber"],
                  "cardType": record["cardType"],
                  "numberOfPorts": record["numberOfPorts"],
                  "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"]}]
            list_of_cards.append(a)
    if refreshState == "initData":
        return "records written"
    return render_template("chassisCardsDetails.html", headers=headers, rows = list_of_cards, ip_tags_dict=ip_tags_dict)


@app.get("/licenseDetails", defaults={'refreshState': "freshPoll"})
@app.get("/licenseDetails/<refreshState>")
def licenseDetails(refreshState):
    headers = ["chassisIP", "chassisType", "hostID", "partNumber", "activationCode", 
               "quantity", "description", "maintenanceDate", "expiryDate"]
    list_of_licenses= []
    
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    if refreshState == "freshPoll"  or refreshState == "initData": 
        for chassis in CHASSIS_LIST:
            out2 = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="licenseDetails")
            list_of_licenses.append(out2)
        write_data_to_database(table_name="license_details_records", records=list_of_licenses)
        
    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="license_details_records")
        for record in records:
            a = [{"chassisIp": record["chassisIp"], 
                  "typeOfChassis": record["typeOfChassis"],
                  "hostId": record["hostId"],
                  "partNumber": record["partNumber"],
                  "activationCode": record["activationCode"],
                  "quantity": record["quantity"],
                  "description": record["description"],
                  "maintenanceDate": record["maintenanceDate"],
                  "expiryDate":record["expiryDate"],
                  "isExpired": record["isExpired"],
                  "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"]}]
            
            list_of_licenses.append(a)
            
    if refreshState == "initData":
        return "records written"
    return render_template("chassisLicenseDetails.html", headers=headers, rows = list_of_licenses)


@app.get("/portDetails", defaults={'refreshState': "freshPoll"})
@app.get("/portDetails/<refreshState>")
def get_chassis_ports_information(refreshState):
    headers = ["chassisIp", "typeOfChassis",
               "cardNumber", "portNumber", "phyMode", "transceiverModel", 
               "transceiverManufacturer", "owner"]
    port_list_details = []
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
        
    if refreshState == "freshPoll" or refreshState == "initData":
        for chassis in CHASSIS_LIST:
            out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="portDetails")
            port_list_details.append(out)
        write_data_to_database(table_name="port_details_records", records=port_list_details)
        
    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="port_details_records")
        for record in records:
            a = [{"chassisIp": record["chassisIp"], 
                  "typeOfChassis": record["typeOfChassis"],
                  "cardNumber": record["cardNumber"],
                  "portNumber": record["portNumber"],
                  "phyMode": record["phyMode"],
                  "transceiverModel": record["transceiverModel"],
                  "transceiverManufacturer": record["transceiverManufacturer"],
                  "owner": record["owner"],
                  "totalPorts":record["totalPorts"],
                  "ownedPorts": record["ownedPorts"],
                  "freePorts": record["freePorts"],
                  "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"]}]
            port_list_details.append(a)    
    
    if refreshState == "initData":
        return "records written"
    return render_template("chassisPortDetails.html", headers=headers, rows = port_list_details)


@app.get("/sensorInformation")
def sensorInformation():

    headers = ["chassisIP", "chassisType", "sensorType", "sensorName", "sensorValue"]
    sensor_list_details = []
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    
    for chassis in CHASSIS_LIST:
            out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="sensorDetails")
            sensor_list_details.append(out)
    return render_template("chassisSensorsDetails.html", headers=headers, rows = sensor_list_details)



@app.post("/addTags")
def addTags():
    input_json = request.get_json(force=True) 
    ip = input_json.get("ip")
    serialNumber = input_json.get("serialNumber")
    tags = input_json.get("tags")
    if ip:
        resp = writeTags(ip, tags, type_of_update="chassis",operation="add")
        
    if serialNumber:
        resp = writeTags(serialNumber, tags, type_of_update="card", operation="add")
        
        
    return resp

@app.post("/removeTags")
def removeTags():
    input_json = request.get_json(force=True) 
    ip = input_json.get("ip")
    serialNumber = input_json.get("serialNumber")
    
    tags = input_json.get("tags")
    if ip:
        resp = writeTags(ip, tags, type_of_update="chassis",operation="remove")
        
    if serialNumber:
        resp = writeTags(serialNumber, tags, type_of_update="card", operation="remove")
    
    return resp
    

def load_base_data():
    """Only load this when getting in through upload portal
    """
    main() # This will delete existing table and create new data
    print(chassisDetails(refreshState="initData"))
    print(cardDetails(refreshState="initData"))
    print(licenseDetails(refreshState="initData"))
    print(get_chassis_ports_information(refreshState="initData"))
    import time; time.sleep(5)