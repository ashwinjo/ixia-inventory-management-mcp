from flask import render_template, request, jsonify, redirect
from app import create_app
from  RestApi.IxOSRestInterface import IxRestSession
from sqlite3_utilities_new import *
from data_poller import controller
import json


app = create_app()

@app.post("/getLogs")
def getlogs():
    CHASSIS_LIST = json.loads(read_username_password_from_database())
    input_json = request.get_json(force=True) 
    chassis_ip = input_json['ip']
    for chassis_item in CHASSIS_LIST:
        if chassis_item["ip"] == chassis_ip:
            chassis = chassis_item
            break
    session = IxRestSession(chassis["ip"], chassis["username"], chassis["password"])
    out = session.collect_chassis_logs(session)
    return jsonify({"resultUrl" : out, "message": "Please login to your chassis and enter this url in browser to download logs"})


@app.get('/uploadConfig')
def uploadConfig():
    return render_template("upload.html")

@app.post('/uploader')
def processInput():
    ip_pw_list = request.form['text']
    write_username_password_to_database(ip_pw_list)
    return redirect('/')
    
@app.post('/setPollingIntervals')
def setPollingIntervals():
    chassis = request.form['chassis']
    cards = request.form['cards']
    ports = request.form['ports']
    sensors = request.form['sensors']
    licensing = request.form['licensing']
    perf = request.form['perf']
    write_polling_intervals_into_database(chassis, cards, ports, sensors, licensing, perf)
    return redirect('/')
    
@app.get('/')
@app.get("/chassisDetails")
def chassisDetails():
    list_of_chassis = []
    headers = ["IP","OS","type","chassisSN","controllerSN", "# PhysicalCards", 
               "IxOS", "IxNetwork Protocols", "IxOS REST",
               "MemoryUsed", "TotalMemory", "%CPU Utilization", "Tags"]

    ip_tags_dict = getTagsFromCurrentDatabase(type_of_update="chassis")
    records = read_data_from_database(table_name="chassis_summary_details")
    for record in records:
        list_of_chassis.append({"chassisIp": record["ip"], 
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
            "os": record["os"]})
    return render_template("chassisDetails.html", headers=headers, rows = list_of_chassis, ip_tags_dict=ip_tags_dict)

    
@app.get("/cardDetails")
def cardDetails():
    list_of_cards = []
    headers = ["chassisIP", "ChassisType", "cardNumber", "serialNumber", "cardType", "numberOfPorts"]
    ip_tags_dict = getTagsFromCurrentDatabase(type_of_update="card")
    records = read_data_from_database(table_name="chassis_card_details")
    for record in records:
        list_of_cards.append([{"chassisIp": record["chassisIp"], 
                "chassisType": record["typeOfChassis"],
                "cardNumber": record["cardNumber"],
                "serialNumber": record["serialNumber"],
                "cardType": record["cardType"],
                "cardState": record["cardState"],
                "numberOfPorts": record["numberOfPorts"],
                "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"]}])
  
    return render_template("chassisCardsDetails.html", headers=headers, rows = list_of_cards, ip_tags_dict=ip_tags_dict)


@app.get("/licenseDetails")
def licenseDetails():
    headers = ["chassisIP", "chassisType", "hostID", "partNumber", "activationCode", 
               "quantity", "description", "maintenanceDate", "expiryDate"]
    list_of_licenses= []
    records = read_data_from_database(table_name="license_details_records")
    for record in records:
        list_of_licenses.append([{"chassisIp": record["chassisIp"], 
                "typeOfChassis": record["typeOfChassis"],
                "hostId": record["hostId"],
                "partNumber": record["partNumber"],
                "activationCode": record["activationCode"],
                "quantity": record["quantity"],
                "description": record["description"],
                "maintenanceDate": record["maintenanceDate"],
                "expiryDate":record["expiryDate"],
                "isExpired": record["isExpired"],
                "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"]}])        
    return render_template("chassisLicenseDetails.html", headers=headers, rows = list_of_licenses)


@app.get("/portDetails")
def get_chassis_ports_information():
    headers = ["chassisIp", "typeOfChassis",
               "cardNumber", "portNumber", "phyMode", "transceiverModel", 
               "transceiverManufacturer", "owner"]
    port_list_details = []

    records = read_data_from_database(table_name="chassis_port_details")
    for record in records:
        port_list_details.append([{"chassisIp": record["chassisIp"], 
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
                "lastUpdatedAt_UTC": record["lastUpdatedAt_UTC"]}])
    return render_template("chassisPortDetails.html", headers=headers, rows = port_list_details)


@app.get("/sensorInformation")
def sensorInformation():
    headers = ["chassisIP", "chassisType", "sensorType", "sensorName", "sensorValue", "unit"]
    sensor_list_details = []
    records = read_data_from_database(table_name="chassis_sensor_details")
    for record in records:
        sensor_list_details.append([{"chassisIp": record["chassisIp"], 
                "typeOfChassis": record["typeOfChassis"],
                "sensorType": record["sensorType"],
                "sensorName": record["sensorName"],
                "sensorValue": record["sensorValue"],
                "unit": record["unit"],
                "lastUpdatedAt_UTC":record["lastUpdatedAt_UTC"]}])
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
    
    

@app.get('/lineChartPerfMetrics')  
@app.get('/lineChartPerfMetrics/<ip>')
def lineChartPerfMetrics(ip):
    
    serv_list = read_username_password_from_database()
    if serv_list:
        CHASSIS_LIST = json.loads(serv_list)
        
    if ip=="fresh":
        return render_template('chassisPerformanceMetrics.html', title='Performance Metrics', 
                            max=100, mem_values=[], 
                            cpu_values=[], 
                            date_timeline_value=[],
                            chassis_list = CHASSIS_LIST)

    elif ip:
        records = get_perf_metrics_from_db(str(ip))
        mem_values = []
        cpu_values = []
        date_timeline_value = []
        chassis_list = []
        for record in records:
            date_timeline_value.append(record['lastUpdatedAt_UTC'])
            mem_values.append(float(record['mem_utilization']))
            cpu_values.append(float(record['cpu_utilization']))
        return render_template('chassisPerformanceMetrics.html', title='Performance Metrics', 
                                max=100, mem_values=mem_values[-10:], 
                                cpu_values=cpu_values[-10:], 
                                date_timeline_value=date_timeline_value[-10:],
                                ip = ip,
                                chassis_list = CHASSIS_LIST)

@app.get("/pollLatestData/<category>")
def pollLatestChassisData(category):
    controller(category_of_poll=category)
    return redirect(categoryToFuntionMap[category]) 

categoryToFuntionMap = {"chassis": "/chassisDetails",
                        "cards": "/cardDetails",
                        "ports": "/portDetails",
                        "licensing": "/licenseDetails",
                        "sensors": "/sensorInformation"}