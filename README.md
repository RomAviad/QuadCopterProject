#General description:

The ground control station is meant to give the operator a command and control interface to the drone.
Its main goals are:
* Supply the operator drone telemetry such as location, altitude and battery levels.
* Provide a simple interface to task assignments to the drone such as scan a perimeter, go to a specified location, etc.
* Be platform independent, easy to use and easy to extend and add new features.
* Be open source ready.

For these reasons a web based application was chosen as the user interface and a python backend server for drone communication and business logic such as map tile server.
A web based application allows easy use in all platforms and the use of python allows for easy portability between systems - can easily run on many supporting operating systems as well as being common open source technologies.



#Components and how they work together
The user interface is a single page application, written in HTML and JavaScript, running on the operator’s browser, communicating with the python Flask based web server running on the ground control station (which can, but doesn’t have to be, the same machine) via HTTP requests.
It contains a OpenLayers based map on which the operator sees the drone as a blue dot and a small data panel of drone data including: Location(GPS lat/long), altitude, orientation and battery level.
The operator can draw routes and perimeter on the map and send them to the drone as a flight plan.


The ground control station runs the python server comprising of a flask web server, map tile server module and a message queue module.
The Flask server serves all the client HTTP requests.
The map tile server provides map tiles from a local cache if they are present or retrieves them from another source (pre-defined server in the WWW). The use of the tile server module enables offline work. before going on a mission the operator can browse the intended area and then all the relevant tiles will be cached and available offline.
The message queue module provides the basis for communication between the drone and the ground control station and as such it runs on both of them.
It is a basic priority queue based on json objects sent via HTTP requests. it also enables to define certain message types as time sensitive so that messages that were not delivered for some reason will be pushed to the back of the line if a newer message from the same type arrives.
This is useful for the following scenario: If a status update was delayed and a newer one is available the old one is irrelevant and we would want to send the most updated status first and the old one later for logging.

#Technology choices in the light of the project goals:

Web-based User Interface - Keeping portability in mind, HTML and JavaScript enable showing the UI on just about any platform out there.
The use of the Bootstrap JS library enables low effort on adapting the UI to mobile devices.

OpenLayers Map - OpenLayers is a modular, JavaScript based, open-source maps project, that enables using tiles from different sources seamlessly on the same map. The OpenLayers community provides many use examples and capabilities that allow a quick ramp-up and a relatively low-effort development.

Python - A common language among open-source communities with a lot of useful built-in libraries. Hence, the online support for any technical issues is really easy to get and is usually based on past knowledge of the community.
The “Flask” micro-framework is based on Python and enables starting a web server really easily with little adjustments and configurations to make before you are “good to go”.

#Future Development suggestions:

Live video streaming - Embed live video that’s broadcasted from the drone in the User Interface, while maintaining high quality of service for the rest the operator features.

Self-Made map tiles - Have the drone to perform a pre-mission flight in the same perimeter it’s supposed to do its mission, in which the drone will take pictures of the terrain from several altitudes, and then by analyzing drone positioning and lens angle -  generate a layer of high resolution tiles for the map.



#Setting up the application:
Please make sure you have the following prerequisites installed/filled prior to trying to run the application:
* Python 2.7 or higher 
  * Preferably 2.x and not 3.x
  * Can be downloaded from https://www.python.org
* Flask micro-framework 
  * Can be downloaded from http://flask.pocoo.org
  * Note: Please make sure you have the flask modules either in the same folder as all the other python files you will be running, or in python’s “lib” folder
* Have your ground control station dedicated machine, operator device (can be the same one or another computer/tablet), and drone connect to the same wireless network. Make sure you have your drone’s IP address so you will be able to connect from the Operator UI.

After the prerequisites above are installed, you should download the content of our git repository from: https://github.com/fselius/GIPdrone/tree/master/QuadCopterServer 

#Running the application:
Assuming you followed the setup instructions above, all you will have to do now is run groundControl.py that you have downloaded from the repository and you will have your ground control server up and running.
Next you would want to access the Operator UI using your web browser by the IP address of the machine running the  server, accessing port 8080. (e.g. if your computer got the local IP of 192.168.1.10, the application would be accessed by the following address: http://192.168.1.10:8080/ )
Note: If you are running the UI on the same machine as you are running the ground control server -  you can also access the UI by the address of http://127.0.0.1:8080/ 
Getting around the UI - 
The first thing you’ll see is a screen with a map on most of it, with an input box on the left for the drone IP. once you will submit that -  the UI will be fully functional and ready to use (get/send data from/to the drone).
The drone would appear on the map as a blue dot.

On the top of the UI you will see a simple menu with the following options (covered from left to right):
* “Auto Update Flight Data” - Clicking this will poll the drone for up to date flight data. Each time the data will be updated you will see the change on the left side of your screen on the flight data area.
You will also notice that once you’ve clicked this option, it would have a darker background to indicate that it’s “on” or “pressed”.
If you will click this button once it’s already pressed, you will turn off the auto update and will no longer receive flight data updates.
* “Map Drawing” - this drop-down menu contains of 4 options:
  * Off (default option) - map drawing is off.
  * LineString - drawing is on and will create a line-string between the points you will click on.
  * Polygon - drawing is on and will create a polygon between the points you will click on.
  * Clear Drawings - clear all the drawings from the map.
	When drawing is turned on, each click on the map will draw a point 
	where you clicked. Upon double-click, an “end drawing” event will be 
	triggered, and a modal dialog will show on your screen asking if you
	would like to send this as a track to the drone.
* “Settings” - Clicking this item would show a modal form on your screen with field to set your critical battery percentage (default as 20%), map center coordinates, and a toggle switch to turn drone following on the map on/off (this option will re-center the map on the moving drone every 5 data updates). After you finish doing your changes in that form you should either click “Save” to apply them, or “Cancel” to ignore them.

Modifying your map drawings - after you have finished drawing and turned drawing off, you can drag drawing points around the map and modify your linestring/polygon. You can also delete points by holding the “shift” key and clicking drawn points (up to a minimal 2-point line-string or a 3-point polygon).
Please note - the current implementation will not resend track data to the drone if it is modified after drawing has ended.

Quick Zoom - When map drawing is off, you can hold the “shift” key and by clicking and dragging the cursor on the map you will get a temporary rectangle drawn on the map. Once the mouse button will be released - the map will zoom in to the rectangle you just finished drawing.

#Developer Notes:

As a developer, you might want to add new API calls to the web server, and might want to extend the capabilities of the default message handling.

Adding new API calls - The server is mostly written as a RESTful API, and should be aspired to be kept that way. Please choose your HTTP methods according to whether you’re going to want to just get data from the server (GET requests) or send data as well (POST requests). Examples of such calls can be found in the groundControl.py file or in the Flask website (found on the prerequisites section).

Extending Message Handling - As the only message handlers provided with the groundControl.py file are handlers for “hello” and “bye” messages, you would want to register your own handlers to use for different message types; This would be done using the “register_handler” function of the groundControl.py module.
Registering a new handler should be according to the enforced interface:
A message kind should have a handler function registered to it, which accepts two mandatory arguments - IP (drone/peer message queue), and message (that would be the actual JSON formatted message). 
Apart from that interface enforcement, you can have your handler do whatever you feel like it should be doing.

JSON objects on the message queue - Message queue messages are formatted as JSON object, these objects have two mandatory fields:
“kind” - Message type, should be a valid type as defined in the priority dictionary in the messageQueue.py module.
“timeStamp” - Message timestamp, formatted to UTC using strftime with the following pattern: %Y-%m-%d %H:%M:%S


