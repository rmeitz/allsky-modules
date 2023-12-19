'''
allsky_weatherflowtempest.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve data from a local personal WeatherFlow Tempest
weather station.

'''
import allsky_shared as s
import os
import requests
import json
from meteocalc import heat_index
from meteocalc import dew_point, Temp

metaData = {
    "name": "WeatherFlow Tempest",
    "description": "Gets weather data from local WeatherFlow Tempest weather station",
    "module": "allsky_weatherflowtempest",
    "events": [
        "periodic"
    ],
    "arguments":{
        "apikey": "",
        "stationid": "",
        "stationnumber": 1,
        "period": 240,
        "expire": 480,
        "filename": "weatherflowtempest.json",
        "units": "imperial"
    },
    "argumentdetails": {
        "apikey": {
            "required": "true",
            "description": "API Key",
            "help": "Your WeatherFlow API key"
        },
        "stationid": {
            "required": "true",
            "description": "Station ID",
            "help": "Your Tempest Station ID"
        },
        "stationnumber": {
            "required": "true",
            "description": "Station Number",
            "help": "If you have more than one station this is the station number.  Default is 1 for a single station."
        },
        "filename": {
            "required": "true",
            "description": "Filename",
            "help": "The name of the file that will be written to the allsky/tmp/extra directory"         
        },        
        "period" : {
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
        "units" : {
            "required": "false",
            "description": "Units",
            "help": "Units of measurement. standard, metric and imperial",
            "type": {
                "fieldtype": "select",
                "values": "standard,metric,imperial"
            }                
        },        
        "expire" : {
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

extraData = {}

def processResult(data, expires, units):
    # setExtraValue("timestamp", data, "WFTIMESTAMP", expires)

    # Temp
    setExtraValue(getTempValue("air_temperature", data, units), "WFAIR_TEMPERATURE", expires)
    setExtraValue(getTempValue("feels_like", data, units), "WFFEELS_LIKE", expires)
    setExtraValue(getTempValue("heat_index", data, units), "WFHEAT_INDEX", expires)
    setExtraValue(getTempValue("wind_chill", data, units), "WFWIND_CHILL", expires)
    setExtraValue(getTempValue("dew_point", data, units), "WFDEW_POINT", expires)
    # setExtraValue("wet_bulb_temperature", data, "WFWETBULBTEMP", expires)

    # Pressure
    setExtraValue(getValue("barometric_pressure", data), "WFPRESSURE", expires)
    # setExtraValue("station_pressure", data, "WFSTATIONPRESSURE", expires)
    # setExtraValue("sea_level_pressure", data, "WFSEALEVELPRESSURE", expires)

    setExtraValue(getValue("relative_humidity", data), "WFREL_HUMIDITY", expires)

    # setExtraValue("precip", data, "WFPRECIP", expires)
    # setExtraValue("precip_accum_last_1hr", data, "WFPRECIPLASTHOUR", expires)
    # setExtraValue("precip_accum_local_day", data, "WFPRECIPLASTDAY", expires)
    # setExtraValue("precip_accum_local_yesterday", data, "WFPRECIPYEStERDAY", expires)
    # setExtraValue("precip_minutes_local_day", data, "WFPRECIPMINDAY", expires)
    # setExtraValue("precip_minutes_local_yesterday", data, "WFPRECIPMINYEStERDAY", expires)

    setExtraValue(getValue("wind_avg", data), "WFWIND_AVG", expires)
    # setExtraValue("wind_direction", data, "WFWINDDIR", expires)
    # setExtraValue("wind_gust", data, "WFWINDGUST", expires)
    # setExtraValue("wind_lull", data, "WFWINDLULL", expires)

    # setExtraValue("solar_radiation", data, "WFSOLORRADIATION", expires)
    # setExtraValue("uv", data, "WFUV", expires)
    setExtraValue(getValue("brightness", data), "WFBRIGHTNESS", expires)

    # setExtraValue("lightning_strike_count", data, "WFLIGHTNINGCOUNT", expires)
    # setExtraValue("lightning_strike_count_last_1hr", data, "WFLIGHTNINGCOUNT1HR", expires)
    # setExtraValue("lightning_strike_count_last_3hr", data, "WFLIGHTNINGCOUNT3HR", expires)

    # setExtraValue("delta_t", data, "WFDELTAT", expires)
    # setExtraValue("air_density", data, "WFAIRDENSITY", expires)


def setExtraValue(value, extraKey, expires):
    global extraData
    # value = getValue(key, data)
    if value is not None:
        extraData[extraKey] = {
            "value": value,
            "expires": expires
        }


def getValue(key, data):
    result = None
    if key in data:
        result = data[key]

    return result

def getTempValue(key, data, units):
    result = None
    if key in data:
        temp = float(data[key])
        t = Temp(temp, 'c')
        if units == "imperial":
            result = round(t.f, 1)
            # s.log(1, "DEBUG: IMPERIAL: {} -> {}".format(temp, result))
        elif units == "metric":
            result = round(t.c, 1)
            # s.log(1, "DEBUG: METRIC: {} -> {}".format(temp, result))
        elif units == "standard":
            result = round(t.k, 1)
            # s.log(1, "DEBUG: STANDARD: {} -> {}".format(temp, result))
    return result


def weatherflowtempest(params, event):
    global extraData    
    result = ""

    expire = int(params["expire"])
    period = int(params["period"])
    apikey = params["apikey"]
    stationid = params["stationid"]
    stationnum = params["stationnumber"]
    fileName = params["filename"]
    module = metaData["module"]
    units = params["units"]

    shouldRun, diff = s.shouldRun(module, period)
    if shouldRun:
        if fileName != "":
            if apikey != "":
                allskyPath = s.getEnvironmentVariable("ALLSKY_HOME")
                if allskyPath is not None:
                    try:
                        resultURL = "https://swd.weatherflow.com/swd/rest/observations/station/{0}?token={1}".format(stationid, apikey)
                        print(resultURL)
                        response = requests.get(resultURL)
                        if response.status_code == 200:
                            data = json.loads(response.content.decode())
                            #s.log(1, "INFO: DEBUG: RAW DATA: " + json.JSONEncoder().encode(data))

                            try:
                                if data['status']['status_code'] != 0:
                                    result = "Data acquired was not successful: " + data['status']['status_message']
                                    s.log(1, "INFO: {}".format(result))

                                elif not 'obs' in data.keys():
                                    result = "Data acquired missing 'obs': " + data
                                    s.log(1, "INFO: {}".format(result))

                                elif len(data['obs']) < int(stationnum):
                                    result = "Data acquired does not have data for station number " + stationnum
                                    s.log(1, "INFO: {}".format(result))

                                else :
                                    #s.log(1, "INFO: DEBUG: STATION: " + stationnum)
                                    obs = data["obs"][int(stationnum) - 1]
                                    #s.log(1, "INFO: DEBUG: OBS: " + json.JSONEncoder().encode(obs))
                                    processResult(obs, expire, units)
                                    s.saveExtraData(fileName,extraData )
                                    result = "Data acquired and written to extra data file {}".format(fileName)
                                    s.log(1,"INFO: {}".format(result))

                            except KeyError:
                                print('Update failed')
                                return

                        else:
                            result = "Got error from WeatherFlow API. Response code {}".format(response.status_code)
                            s.log(0,"ERROR: {}".format(result))
                    except Exception as e:
                        result = str(e)
                        s.log(0, "ERROR: {}".format(result))
                else:
                    result = "Cannot find ALLSKY_HOME Environment variable"
                    s.log(0,"ERROR: {}".format(result))                    
            else:
                result = "Missing WeatherFlow API key"
                s.log(0,"ERROR: {}".format(result))
        else:
            result = "Missing filename for data"
            s.log(0,"ERROR: {}".format(result))

        s.setLastRun(module)
    else:
        result = "Last run {} seconds ago. Running every {} seconds".format(diff, period)
        s.log(1,"INFO: {}".format(result))

    return result

def weatherflowtempest_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "weatherflowtempest.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)