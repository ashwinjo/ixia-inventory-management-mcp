create_chassis_summary_sql = """CREATE TABLE IF NOT EXISTS chassis_summary_details (
                                ip VARCHAR(255) NOT NULL,
                                chassisSN TEXT,
                                controllerSN TEXT,
                                type_of_chassis TEXT,
                                physicalCards TEXT,
                                status_status TEXT,
                                ixOS TEXT,
                                ixNetwork_Protocols TEXT,
                                ixOS_REST TEXT,
                                tags TEXT,  
                                lastUpdatedAt_UTC TEXT,
                                mem_bytes TEXT, 
                                mem_bytes_total TEXT, 
                                cpu_pert_usage TEXT,
                                os TEXT
                                );"""
                            
                                            
create_card_details_records_sql = """CREATE TABLE IF NOT EXISTS chassis_card_details (
                                        'chassisIp' VARCHAR(255) NOT NULL,
                                        'typeOfChassis' TEXT,
                                        'cardNumber' TEXT,
                                        'serialNumber' TEXT,
                                        'cardType' TEXT,
                                        'cardState' TEXT,
                                        'numberOfPorts' TEXT, 
                                        'tags' TEXT, 
                                        'lastUpdatedAt_UTC' TEXT
                                        );"""
                                        
create_port_details_records_sql = """CREATE TABLE IF NOT EXISTS chassis_port_details (
                                        'chassisIp' VARCHAR(255) NOT NULL,
                                        'typeOfChassis' TEXT,
                                        'cardNumber' TEXT,
                                        'portNumber' TEXT,
                                        'phyMode' TEXT,
                                        'linkState' TEXT,
                                        'transceiverModel' TEXT,
                                        'transceiverManufacturer' TEXT,
                                        'owner' TEXT,
                                        'speed' TEXT, 
                                        'type' TEXT,
                                        'totalPorts' TEXT,  
                                        'ownedPorts' TEXT,
                                        'freePorts' TEXT,
                                        'lastUpdatedAt_UTC' TEXT
                                        );"""
                                        
create_license_details_records_sql = """CREATE TABLE IF NOT EXISTS license_details_records (
                                            'chassisIp'VARCHAR(255) NOT NULL,
                                            'typeOfChassis' TEXT,
                                            'hostId' TEXT,
                                            'partNumber' TEXT,
                                            'activationCode' TEXT,
                                            'quantity' TEXT,
                                            'description' TEXT,
                                            'maintenanceDate' TEXT,
                                            'expiryDate' TEXT,
                                            'isExpired' TEXT,
                                            'lastUpdatedAt_UTC' TEXT
                                            );"""
                                            

create_sensor_details_sql = """CREATE TABLE IF NOT EXISTS chassis_sensor_details (
                                chassisIp VARCHAR(255) NOT NULL,
                                typeOfChassis TEXT ,
                                sensorType TEXT ,
                                sensorName TEXT,
                                sensorValue TEXT,
                                unit TEXT,
                                lastUpdatedAt_UTC TEXT
                                );"""
                                            
create_usage_metrics = """CREATE TABLE IF NOT EXISTS chassis_utilization_details (
                                            chassisIp VARCHAR(255) NOT NULL,
                                            mem_utilization TEXT, 
                                            cpu_utilization TEXT,
                                            lastUpdatedAt_UTC TEXT
                                            );"""
                                            

create_ip_tags_sql = """CREATE TABLE IF NOT EXISTS user_ip_tags (
                                ip VARCHAR(255) NOT NULL,
                                tags TEXT
                                );"""
                                
create_card_tags_sql = """CREATE TABLE IF NOT EXISTS user_card_tags (
                                serialNumber VARCHAR(255) NOT NULL,
                                tags TEXT
                                );"""
                                
create_perf_metrics_sql = """CREATE TABLE IF NOT EXISTS perf_metrics (
                                ip VARCHAR(255) NOT NULL,
                                mem_bytes TEXT ,
                                mem_bytes_total TEXT ,
                                cpu_pert_usage TEXT
                                );"""
                                
create_usenname_password_table = """CREATE TABLE IF NOT EXISTS user_db (
                                ixia_servers_json TEXT
                                );"""

create_poll_settings_table = """CREATE TABLE IF NOT EXISTS poll_setting (
                                chassis INTEGER,
                                cards INTEGER ,
                                ports INTEGER,
                                sensors INTEGER ,
                                perf INTEGER,
                                licensing INTEGER,
                                alertMonitor INTEGER
                                );"""