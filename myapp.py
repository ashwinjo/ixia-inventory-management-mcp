from flask import render_template, request, jsonify, redirect
from app import create_app
from IxOSRest_charter import start_chassis_rest_data_fetch as scrdf
from  RestApi.IxOSRestInterface import IxRestSession
from werkzeug.utils import secure_filename
import sqlite3

app = create_app()

# @app.get("/oldChassisDetails")
# def chassisDetails():
#     try:
#         from config import CHASSIS_LIST
#     except Exception:
#         CHASSIS_LIST = []
#     list_of_chassis_information = []
#     img_link = ""
#     list_of_available_chassis_types= []
#     if CHASSIS_LIST:
#         for idx, chassis in enumerate(CHASSIS_LIST):
#             complete_chassis_repsonse = start_chassis_rest_data_fetch(chassis["ip"], chassis["username"], chassis["password"])
            
#             complete_chassis_repsonse["chassis_information"].update({"chassisName": f"Chassis{idx+1}"})
#             if "XGS12" in complete_chassis_repsonse["chassis_information"]["type"]:
#                 img_link = "https://cdn.cs.1worldsync.com/50/53/5053b84f-311b-4f29-bf7e-2d451293a688.jpg"
#             elif "Ixia PerfectStorm One" in complete_chassis_repsonse["chassis_information"]["type"]:
#                 img_link = "https://keysight-h.assetsadobe.com/is/image/content/dam/keysight/en/img/prd/network-test/ixia/network-test-hardware/perfectstorm-one1/Allmodels_right_PerfectStormONE-40G_870-0128_L20-550x550.png"
#             elif "XGS2" in complete_chassis_repsonse["chassis_information"]["type"]:
#                 img_link = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRduxtkTM6vPYDHhwlUUse8Np4_Zd5xTeuJNa_G9wJyUw&s"
#             elif "Ixia Virtual Test Appliance" in complete_chassis_repsonse["chassis_information"]["type"]:
#                 img_link = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTJEZ8qzIPaSZbld6HkjbcGXg9Eb51DT5HN7aRZVQzPn2Myo93Onq7PXtWMglYnTnMqy3c&usqp=CAU"
#             elif "AresONE" in complete_chassis_repsonse["chassis_information"]["type"]:
#                 img_link = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsSpRIJSWrDlzpzaNg9URqT3IOfqZPAGrdNOWA0w0MpeVhpU1E9-nhws6GgYdr53Gcmc4&usqp=CAU"
#             elif "Novus" in complete_chassis_repsonse["chassis_information"]["type"]:
#                 img_link = "https://www.keysight.com/content/dam/keysight/en/img/prd/network-test/ixia/network-test-hardware/novus-one-plus-3-5-speed-l2-7-fixed-chassis/NovusOneRight-700px.png?"
                
#             list_of_available_chassis_types.append(complete_chassis_repsonse["chassis_information"]["type"].replace(" ", "_"))
#             complete_chassis_repsonse["chassis_information"].update({"chassis_model_img_src": img_link})
#             list_of_chassis_information.append(complete_chassis_repsonse)

#     return render_template("index.html", data=list_of_chassis_information, type_list= list(set(list_of_available_chassis_types)))

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
      return redirect("/", code=302)
  
@app.post('/goDirectToHome')
def goDirectToHome():
    return redirect("/", code=302)

@app.get("/")
def chassisSummary():
    try:
        from config import CHASSIS_LIST
    except Exception:
        import init_db
        CHASSIS_LIST = []
    
    l = [] 
    fl = []
    if CHASSIS_LIST:  
        for chassis in CHASSIS_LIST:
            out = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="chassisSummary")
            l.append(out)
                
        for record in l:
            fl.append(list(record.values()))
        
        headers=list(l[0].keys())
    else:
        headers = ["IP","type","chassisSN","controllerSN", "# PhysicalCards"]
    ip_tags_dict = _getTagsFromCurrentDatabase()
    return render_template("chassisDetails.html", headers=headers, rows = fl, ip_tags_dict=ip_tags_dict)


@app.get("/portDetails")
def get_chassis_ports_information():
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    l= []
    for chassis in CHASSIS_LIST:
        out1 = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="portDetails")
        l.append(out1)
        
        
    fl = []
    headers = ""
    for cd in l:
        print(cd)
        list_of_ports = cd["portDetails"]
        list_of_ports.append(cd["used_ports"])
        list_of_ports.append(cd["total_ports"])
        list_of_ports.append(cd["ctype"])
        list_of_ports.append(cd["ip"])
        fl.append(list_of_ports)
        headers = ["cardNumber", "portNumber", "phyMode", "transceiverModel", "transceiverManufacturer", "owner"]
    return render_template("chassisPortDetails.html", headers=headers, rows = fl)
    

@app.get("/cardDetails")
def cardDetails():
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    l= []
    for chassis in CHASSIS_LIST:
        out1 = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="cardDetails")
        l.append(out1)
        
    fl = []
    headers = ""
    """[{
        'cardDetails': [{
        'cardNumber': 1,
        'type': 'Ixia Virtual Load Module',
        'numberOfPorts': 1
        }],
        'ip': 'ec2-44-205-197-56.compute-1.amazonaws.com'
        }, {
        'cardDetails': [{
        'cardNumber': 1,
        'type': 'Ixia Virtual Load Module',
        'numberOfPorts': 1
        }],
        'ip': 'ec2-44-207-84-108.compute-1.amazonaws.com'
        }]
    """
    for cd in l:
        list_of_cards = cd["cardDetails"]
        list_of_cards.append(cd["ctype"])
        list_of_cards.append(cd["ip"])
        fl.append(list_of_cards)
        if not headers:
            if len(list_of_cards) > 1:
                headers = list(list_of_cards[0].keys())
            else:
                headers = ["cardNumber", "serialNumber", "type", "numberOfPorts"]
    return render_template("chassisCardsDetails.html", headers=headers, rows = fl)

@app.get("/licenseDetails")
def licenseDetails():
    try:
        from config import CHASSIS_LIST
    except Exception:
        CHASSIS_LIST = []
    l= []
    for chassis in CHASSIS_LIST:
        out2 = scrdf(chassis["ip"], chassis["username"], chassis["password"], operation="licenseDetails")
        l.append(out2)
        
    fl = []
    headers = ""
    
    for cd in l:
        list_of_cards = cd["licenseDetails"]
        list_of_cards.append(cd["hostId"])
        list_of_cards.append(cd["ctype"])
        list_of_cards.append(cd["ip"])
        fl.append(list_of_cards)
        if not headers:
            if len(list_of_cards) > 1:
                headers = list(list_of_cards[0].keys())
            else:
                headers = ["activationCode", "quantity", "description", "expiryDate"]
    return render_template("chassisLicenseDetails.html", headers=headers, rows = fl)


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
    

def _get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def _writeTags(ip, tags, operation=None):
    str_currenttags = ""
    ip_tags_dict = _getTagsFromCurrentDatabase()
    currenttags = ip_tags_dict.get(ip)
    new_tags =  tags.split(",")
   
    conn = _get_db_connection()
    cur = conn.cursor()
    if currenttags: # There is a record present
        if operation == "add":
            str_currenttags = ",".join(currenttags+new_tags)
        elif operation == "remove":
            for t in new_tags:
                currenttags.remove(t)
            str_currenttags = ",".join(currenttags)
        cur.execute(f"UPDATE user_ip_tags SET tags = '{str_currenttags}' where ip = '{ip}'")
    else: # New Record
        cur.execute(f"INSERT INTO user_ip_tags (ip, tags) VALUES ('{ip}', '{tags}')")
    conn.commit()
    cur.close()
    conn.close()
    return "Records successfully updated"
        
def _getTagsFromCurrentDatabase():
    ip_tags_dict = {}
    conn = _get_db_connection()
    cur = conn.cursor()
    posts = cur.execute(f"SELECT * FROM user_ip_tags").fetchall()
    cur.close()
    conn.close()
    for post in posts:
        ip_tags_dict.update({post["ip"]: post["tags"].split(",")})
    return ip_tags_dict