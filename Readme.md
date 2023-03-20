Ixia Inventory Explorer is Flask based tool for managing all Ixia Inventory that user might have from a single UI.
Project is UI written over open IxOS API's that we can find at https://github.com/OpenIxia/IxOS/tree/master/Utilities/Python

REST API references at

https://(chassisIp)/chassis/swagger/index.html?v=1.3.0.822#/
https://(chassisIp)/platform/swagger/index.html?v=1.3.0.822#/



Why use this ?
==

 - Lab Ixia Inventory Explorer tool for Administrators/ NE’s/ SE’s.
 - Chassis, Cards, Ports, Licensing, Sensor, Chassis Utilization Metrics all under one tool. 
 - Ability to be deployed on-prem since it is docker  containerized.

Functionality
==

Ixia Inventor Explorer offers a range of features that make it an ideal tool for lab network engineers, lab administrators, and Keysight SE’s.

Some of the key features include:

• Unified preview of available Ixia Chassis with custom tagging feature
• License statistics for every Ixia Chassis 
• Card Statistics with custom tagging feature
• Port Statistics for owner, type of optic
• One-click IxOS chassis log collection
• Download Statistics as csv for Ixia Support Team 
• On-demand data refresh 
•Column based filtering.

Prerequisites
==
* Linux Server with docker installed
* Linux server with internet access to Dockerhub CR
* 


Installation:
==

**Pull Docker Image.** 
docker pull ashjo317/ixia:ixinventorymanager.0.0.11
**Run Docker Image.** 
docker run -d –p 80:3000 ashjo317/ixia:ixinventorymanager. 0.0.11

  

Disclaimer:
==
Please note that the Python-based tool provided here is offered as-is, without any warranty or guarantee of fitness for any particular purpose. The author of this tool will not be able to provide support for feature requests, bug fixes, or any other modifications to the code. However, customers are welcome to use the code provided and modify it as they see fit for their own use.

For feedback please reach out to ashwin.joshi@keysight.com