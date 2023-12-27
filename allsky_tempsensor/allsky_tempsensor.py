'''
allsky_tempsensor.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve data from a local file written by a script that reads
ad temperature/humidity sensor in the AllSky unit.  The file is in the WEBUI_DATA
file format from the AllSky documentation.

'''
import allsky_shared as s
import os

metaData = {
    "name": "Temperature/Humidity Sensor",
    "description": "Gets data from a internal temperature/humidity sensor.",
    "module": "allsky_tempsensor",
    "events": [
        "periodic"
    ],
    "arguments": {
        "datafile": "/home/admin/tmpsensor/temp_sensor_data.txt",
        "period": 300,
        "expire": 600,
        "filename": "tempsensor.json",
    },
    "argumentdetails": {
        "datafile": {
            "required": "true",
            "description": "Datafile (full path)",
            "help": "The full path to your data file that contains the sensor data."
        },
        "filename": {
            "required": "true",
            "description": "Filename",
            "help": "The name of the file that will be written to the allsky/tmp/extra directory"
        },
        "period": {
            "required": "true",
            "description": "Read Every",
            "help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",
            "type": {
                "fieldtype": "spinner",
                "min": 60,
                "max": 1440,
                "step": 1
            }
        },
        "expire": {
            "required": "true",
            "description": "Expiry Time",
            "help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
            "type": {
                "fieldtype": "spinner",
                "min": 61,
                "max": 1500,
                "step": 1
            }
        }
    }
}


def tempsensor(params, event):
    data = {}

    expire = int(params["expire"])
    period = int(params["period"])
    fileName = params["filename"]
    module = metaData["module"]
    datafile = params["datafile"]

    shouldRun, diff = s.shouldRun(module, period)
    if shouldRun:
        if fileName != "" and datafile != "":
            allskyPath = s.getEnvironmentVariable("ALLSKY_HOME")
            if allskyPath is not None:
                try:
                    with open(datafile, "r") as file:
                        for line in file.read():
                            substr = line.strip().split("\t")
                            if substr[0] == "data":
                                if substr[2] == "Internal Temperature":
                                    data["INTERNALTEMPERATURE"] = substr[3]
                            elif substr[0] == "progress":
                                if substr[2] == "Internal Humidity":
                                    data["INTERNALHUMIDITY"] = substr[3]
                    s.saveExtraData(fileName, data)
                    result = "Data acquired and written to extra data file {}".format(fileName)
                    s.log(1, "INFO: {}".format(result))

                except Exception as e:
                    result = str(e)
                    s.log(0, "ERROR: updating temp/humidity sensor: {}".format(result))

    s.setLastRun(module)

    result = "Last run {} seconds ago. Running every {} seconds".format(diff, period)
    s.log(1, "INFO: {}".format(result))

    return result


def tempsensor_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "tempsensor.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
