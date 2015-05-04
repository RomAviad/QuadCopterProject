/** On load execution: * */

var map = null;
var drawInteraction = null;
var drawOverlay = null;
var autoUpdate = false;
var followDrone = false;
var followIterator = 0;
var criticalBatteryLevel = 20;

/** Global placeholder for polygon/linestring coordinates **/
var currentDrawLat = [];
var currentDrawLon = [];
var currentDrawType = "";


$(document).ready(init);

/** End of on load execution: * */

/** Functions * */

/**
 * INITIALIZE (performed on application page load)
 */
function init() {
    $("#settings").click(fillSettingsModal);
    $("#followToggle").click(onFollowToggle);
    $("#saveSettings").click(onSaveSettings);
    $("#sendDroneIp").click(sendDroneIp);
    $("#dontSendTrack").click(clearTrackData);
    $("#sendTrack").click(sendTrackData);
    $(window).resize(fixMapSize);
    map = createMap();
    drawOverlay = createOverlay();
    drawOverlay.setMap(map);
    map.addInteraction(createModifyInteaction(drawOverlay));
    setInterval(updateDroneLocation, 300);
    fixMapSize();
}

/** Map creation and definition functions  **/
/**
 * Create the map object
 * @returns {ol.Map}
 */
function createMap() {
    return new ol.Map({
        layers : [ createSatLayer(), createDroneLayer() ],
        target : 'map',
        controls : new ol.Collection([ createMousePositionControl() ]),
        view : new ol.View({
            center : [ 3898184, 3865621 ],
            zoom : 15
        })
    });
}

/**
 * Create the mouse position control for the map to allow
 * displaying cursor coordinates on the app screen
 * @returns {OpenLayers.Control.MousePosition}
 */
function createMousePositionControl() {
    return new ol.control.MousePosition({
        coordinateFormat : ol.coordinate.createStringXY(5),
        // projection : 'EPSG:3857',
        projection : 'EPSG:4326',
        undefinedHTML : '&nbsp;',
        // Define this so position is not set by default css
        className : 'custom-mouse-position',
        // Choose specific element to attach to
        target : document.getElementById('mouse_location'),
    });
}

/**
 * Create the map layer that holds the drone icon
 * @returns {OpenLayers.Feature.Vector}
 */
function createDroneLayer() {
    var iconFeature = new ol.Feature({
        geometry : projectLatLong(35.01574, 32.77849)
    });

    iconFeature.setStyle(new ol.style.Style({
        image : new ol.style.Icon(/** @type {olx.style.IconOptions} */
            ({
                anchor : [ 0.9, 80 ],
                anchorXUnits : 'fraction',
                anchorYUnits : 'pixels',
                opacity : 0.75,
                src : 'images/drone.png'
            }))
    }));
    return new ol.layer.Vector({
        source : new ol.source.Vector({
            features : [ iconFeature ]
        })
    });
}

/**
 * Create the map layer that holds satellite map tiles
 * (note: this is made by our choice, you can put whatever
 *        tiles you want from virtually any tile server)
 * @returns {OpenLayers.Tile}
 */
function createSatLayer() {
    var satTileServer = "http://" + location.host
        + "/tiles/sat/{z}/{x}/{y}.jpg";
    return new ol.layer.Tile({
        source : new ol.source.XYZ({
            urls : [ satTileServer, satTileServer, satTileServer ]
        })
    });
}


/**
 * The features are not added to a regular vector layer/source,
 * but to a feature overlay which holds a collection of features.
 * This collection is passed to the modify and also the draw
 * interaction, so that both can add or modify features.
 * @returns {ol.FeatureOverlay}
 */
function createOverlay() {
    return new ol.FeatureOverlay({
        style : new ol.style.Style({
            fill : new ol.style.Fill({
                color : 'rgba(255, 255, 255, 0.15)'
            }),
            stroke : new ol.style.Stroke({
                color : '#ffcc33',
                width : 2
            }),
            image : new ol.style.Circle({
                radius : 5,
                fill : new ol.style.Fill({
                    color : '#ffcc33'
                })
            })
        })
    });
}


/**
 * Getter for the drone icon feature
 * @returns {*}
 */
function getDroneFeature() {
	return map.getLayers().getArray()[1].getSource().getFeatures()[0];
}

/**
 * convert the given latitude and longitude  from EPSG:4326 format
 * to EPSG:3857 format
 * @param lat
 * @param long
 * @returns {Zj.Point}
 */
function projectLatLong(lat, long) {
	return new ol.geom.Point(ol.proj.transform([ lat, long ], 'EPSG:4326',
			'EPSG:3857'));
}


function createModifyInteaction(overlay) {
    return new ol.interaction.Modify({
        features : overlay.getFeatures(),
        // the SHIFT key must be pressed to delete vertices, so
        // that new vertices can be drawn at the same position
        // of existing vertices
        deleteCondition : function(event) {
            return ol.events.condition.shiftKeyOnly(event)
                && ol.events.condition.singleClick(event);
        }
    });
}

function createDrawInteraction(overlay, drawType) {
    return new ol.interaction.Draw({
        features : overlay.getFeatures(),
        /** @type {ol.geom.GeometryType} */
        type : drawType
    });
}


/** END OF MAP CREATION **/

/** Application Functions and helpers **/

/**
 * Updates the drone feature location on the map
 */
function updateDroneLocation() {
	if (!autoUpdate) {
		return;
	}
	jQuery.getJSON("../flightData", function(data) {
		getDroneFeature().setGeometry(projectLatLong(data.lat, data.long));
		$("#lat").html(data.lat.toFixed(5));
		$("#long").html(data.long.toFixed(5));
		$("#height").html(data.height.toFixed(2));
		$("#orientation").html(data.orientation.toFixed(2));
		batteryLevel = data.battery.toFixed(1);
		$("#battery").html(batteryLevel);
		$("#battery").toggleClass("criticalLevel", batteryLevel <= criticalBatteryLevel);
	});
	if (followDrone) {
	    followIterator++;
	    followIterator = followIterator%5;
	    if (followIterator == 0) {
            var lat = parseFloat($("#lat").html());
            var lon = parseFloat($("#long").html());
            map.getView().setCenter(ol.proj.transform([lat, lon], 'EPSG:4326', 'EPSG:3857'));
	    }
	}
}

/**
 * Toggle the auto-update button to look "pressed" (or not)
 */
function toggleAutoUpdateFlightData() {
	autoUpdate = !autoUpdate;
	$(this).toggleClass("active", autoUpdate);
}

//ToDo: figure out if we need to remove this function or not
function createSelectInteraction(overlay) {
	return new ol.interaction.Select({
		features : overlay.getFeatures(),
		removeCondition : function(event) {
			return ol.events.condition.altKeyOnly(event)
			&& ol.events.condition.singleClick(event);
		}
	});
}

/**
 *  Double click validator
 */
function coordinatesExist(lat, lon) {
    var sameLat = currentDrawLat[currentDrawLat.length - 1] == lat;
    var sameLon = currentDrawLon[currentDrawLon.length - 1] == lon;
    return sameLat && sameLon;
}

/**
 * Event handler for map drawing clicks
 * adds the coordinates of the click to the global coordinates arrays
 * @param event - click event
 */
function addDrawCoordinates(event) {
    var mousePositionString = $("#mouse_location").find("div.custom-mouse-position").text();
    var positionSplit = mousePositionString.split(", ");
    var lat = parseFloat(positionSplit[0]);
    var lon = parseFloat(positionSplit[1]);
    if (coordinatesExist(lat, lon)) {
    	return;
    }
    currentDrawLat.push(lat);
    currentDrawLon.push(lon);
}

/**
 * Event handler for finishing a drawing (with a double-click)
 * This handler pops-up a modal dialog that asks the user if he
 * wants to send the drawing to the drone or just leave it on the map.
 */
function finishDrawing() {
    $("#drawSendModal").modal('toggle');
}

/**
 * Send the drawing coordinates to the server via HTTP POST request.
 */
function sendTrackData() {
    var points = [];
    for (var i = 0; i < currentDrawLat.length; i++) {
        var point = {"lat":currentDrawLat[i], "lon":currentDrawLon[i]};
        points.push(point);
    }
    $.post('../track', {"drawType": currentDrawType, "drawCoordinates":JSON.stringify(points)});
    clearTrackData();
    $("#drawSendModal").modal('toggle');
}

/**
 * Clear the globals used to keep current drawing coordinates
 * after we finish
 */
function clearTrackData() {
    currentDrawLat = [];
    currentDrawLon = [];
}

/**
 * Event handler for click on the "off" link in the
 * map drawing drop-down menu
 * @param event
 */
function onDrawOff(event) {
	if (drawInteraction == null) {
		return;
	}
	$(map).unbind("dblclick", finishDrawing);
	$(map).unbind("click", addDrawCoordinates);
	map.removeInteraction(drawInteraction);
	drawInteraction = null;
    currentDrawType = "";
	return;
}

/**
 * Event handler for click on the "clear drawing" link in the
 * map drawing drop-down menu
 * @param event
 */
function onClearDrawings(event) {
	drawOverlay.getFeatures().clear();
}

/**
 * Event handler for click on the "Polygon" link in the
 * map drawing drop-down menu
 * @param event
 */
function onDrawPolygon(event) {
	onDrawOff(event);
    currentDrawType = "Polygon";
	drawInteraction = createDrawInteraction(drawOverlay, "Polygon");
	map.addInteraction(drawInteraction);
	$(map).click(addDrawCoordinates);
    $(map).dblclick(finishDrawing);
}

/**
 * Event handler for click on the "LineString" link in the
 * map drawing drop-down menu
 * @param event
 */
function onDrawLineString(event) {
	onDrawOff(event);
    currentDrawType = "LineString";
	drawInteraction = createDrawInteraction(drawOverlay, "LineString");
	map.addInteraction(drawInteraction);
    $(map).click(addDrawCoordinates);
    $(map).dblclick(finishDrawing);
}

/**
 * Set the application to follow and re-center the map
 * on the drone
 */
function setFollowToggle() {
    if (followDrone) {
        $("#followToggle").attr("aria-pressed", "true");
        $("#followToggle").attr("tooltip", "Currently centering map on drone movement");
        $("#followToggle").text("On");
    }
    else {
        $("#followToggle").attr("aria-pressed", "false");
        $("#followToggle").attr("tooltip", "Currently not centering map on drone movement");
        $("#followToggle").text("Off");
    }
}

/**
 * Fill the settings modal dialog with relevant information
 * @param event
 */
function fillSettingsModal(event) {
    $("#criticalBattery").val(criticalBatteryLevel);
    var center = ol.proj.transform(map.getView().getCenter(), 'EPSG:3857', 'EPSG:4326');
    $("#mapCenterLat").val(center[0]);
    $("#mapCenterLon").val(center[1]);
    setFollowToggle();
}

/**
 * Toggle the the follow flag to follow and re-center the map on the drone
 * @param event
 */
function onFollowToggle(event) {
    followDrone = !followDrone;
    setFollowToggle();
}

/**
 * Event handler for "save" click on the settings modal dialog
 * @param event
 */
function onSaveSettings(event) {
    var formLat = parseFloat($("#mapCenterLat").val());
    var formLon = parseFloat($("#mapCenterLon").val());
    criticalBatteryLevel = parseFloat($("#criticalBattery").val());
    map.getView().setCenter(ol.proj.transform([formLat, formLon], 'EPSG:4326', 'EPSG:3857'));
    $("#closeSettings").click();
}

/**
 * Fix the map size on window resize
 */
function fixMapSize() {
	//required so that size fix occurs after resize event is finished
	setTimeout(function() {
		h = $(window).height() - 90;
		w = $(window).width() - 270; 
		map.setSize([w, h]);
	}, 300);
}

/**
 * Enable NavBar items upon sending a drone IP
 */
function enableNavbarItems() {
    $("#autoUpdateFlightData").removeClass("disabled");
    $("li.dropdown").removeClass("disabled");
    $("#drawOff").removeClass("disabled");
    $("#drawLineString").removeClass("disabled");
    $("#drawPolygon").removeClass("disabled");
    $("#clearDrawings").removeClass("disabled");
    $("#autoUpdateFlightData").click(toggleAutoUpdateFlightData);
    $("#drawOff").click(onDrawOff);
    $("#clearDrawings").click(onClearDrawings);
    $("#drawPolygon").click(onDrawPolygon);
    $("#drawLineString").click(onDrawLineString);
}

/**
 * Send drone IP to server
 */
function sendDroneIp() {
    $.get("../changeDrone?ip=" + $("#droneIp").val(), function(data) {
		if(data == "ok") {
			$("#flight_data").css("display","block");
			$("#registerDrone").css("display", "none");
            enableNavbarItems();
		}
	});
}
