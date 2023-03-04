from flask import render_template, request, jsonify, redirect
from app import create_app
from IxOSRest_charter import start_chassis_rest_data_fetch as scrdf
from  RestApi.IxOSRestInterface import IxRestSession
from werkzeug.utils import secure_filename
from sqlite3_utilities import read_data_from_database, write_data_to_database, _getTagsFromCurrentDatabase, _writeTags
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


@app.get('/upload')
def upload_file():
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
    return redirect("/fromDBPoll", code=302)
  
@app.post('/goDirectToHome')
def goDirectToHome():
    return redirect("/", code=302)

@app.get("/", defaults={'refreshState': "freshPoll"})
@app.get("/<refreshState>")
def chassisSummary(refreshState):
    headers = ["IP","type","chassisSN","controllerSN", "# PhysicalCards", "Status", "IxOS", "IxNetwork Protocols", "IxOS REST"]
    try:
        from config import CHASSIS_LIST
    except Exception:
        # This will create the blank tables for you the first time you load the application
        main()
        CHASSIS_LIST = []
    
    l = [] 
    fl = []
    ip_tags_dict = _getTagsFromCurrentDatabase()
    if refreshState == "freshPoll": 
        if CHASSIS_LIST:  
            for chassis in CHASSIS_LIST:
                out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="chassisSummary")
                l.append(out)
        
            for record in l:
                fl.append(list(record.values()))
            write_data_to_database(table_name="chassis_summary_records", records=fl, ip_tag_list=ip_tags_dict)
            
    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="chassis_summary_records")
        print(records)
        for record in records:
            a = [record["ip"], record["chassisSN"],record["controllerSN"],
                 record["type_of_chassis"],record["physicalCards"],record["status_status"],record["lastUpdatedAt_UTC"],
                 record["ixOS"],record["ixNetwork_Protocols"],record["ixOS_REST"], record["tags"]]
            
            fl.append(a)

    print(fl, ip_tags_dict)
    return render_template("chassisDetails.html", headers=headers, rows = fl, ip_tags_dict=ip_tags_dict, oprn=refreshState)



    
@app.get("/cardDetails", defaults={'refreshState': "freshPoll"})
@app.get("/cardDetails/<refreshState>")
def cardDetails(refreshState):
    headers = ["chassisIP", "ChassisType", "cardNumber", "serialNumber", "cardType", "numberOfPorts"]
    list_of_cards= []
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    
    if refreshState == "freshPoll": 
        for chassis in CHASSIS_LIST:
            out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="cardDetails")
            list_of_cards.append(out)
        write_data_to_database(table_name="cards_details_records", records=list_of_cards)

    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="cards_details_records")
        for record in records:
            print(record["chassisIp"])
            a = [{"chassisIp": record["chassisIp"], 
                  "chassisType": record["typeOfChassis"],
                  "cardNumber": record["cardNumber"],
                  "serialNumber": record["serialNumber"],
                  "cardType": record["cardType"],
                  "numberOfPorts": record["numberOfPorts"],
                  "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"]}]
            list_of_cards.append(a)
    return render_template("chassisCardsDetails.html", headers=headers, rows = list_of_cards)


@app.get("/licenseDetails", defaults={'refreshState': "freshPoll"})
@app.get("/licenseDetails/<refreshState>")
def licenseDetails(refreshState):
    headers = ["chassisIP", "chassisType", "hostID", "partNumber", "activationCode", 
               "quantity", "description", "maintenanceDate", "expiryDate", "isExpired"]
    list_of_licenses= []
    
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    print(refreshState)
    if refreshState == "freshPoll": 
        for chassis in CHASSIS_LIST:
            out2 = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="licenseDetails")
            list_of_licenses.append(out2)
        write_data_to_database(table_name="license_details_records", records=list_of_licenses)
        
    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="license_details_records")
        print(records)
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
    return render_template("chassisLicenseDetails.html", headers=headers, rows = list_of_licenses)


@app.get("/portDetails", defaults={'refreshState': "freshPoll"})
@app.get("/portDetails/<refreshState>")
def get_chassis_ports_information(refreshState):
    headers = ["chassisIp", "typeOfChassis", "ownedPorts", "freePorts", "totalPorts",
               "cardNumber", "portNumber", "phyMode", "transceiverModel", 
               "transceiverManufacturer", "owner"]
    port_list_details = []
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
        
    if refreshState == "freshPoll":
        for chassis in CHASSIS_LIST:
            out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="portDetails")
            port_list_details.append(out)
        write_data_to_database(table_name="port_details_records", records=port_list_details)
        
    elif refreshState == "fromDBPoll":
        records = read_data_from_database(table_name="port_details_records")
        print(records)
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
    
    return render_template("chassisPortDetails.html", headers=headers, rows = port_list_details)


@app.post("/addTags")
def addTags():
    input_json = request.get_json(force=True) 
    ip = input_json["ip"]
    tags = input_json["tags"]
    resp = _writeTags(ip, tags, operation="add")
    return resp

@app.post("/removeTags")
def removeTags():
    input_json = request.get_json(force=True) 
    ip = input_json["ip"]
    tags = input_json["tags"]
    resp = _writeTags(ip, tags, operation="remove")
    
    return resp
    

def load_base_data():
    chassisSummary(refreshState="freshPoll")
    cardDetails(refreshState="freshPoll")
    licenseDetails(refreshState="freshPoll")
    get_chassis_ports_information(refreshState="freshPoll")
    