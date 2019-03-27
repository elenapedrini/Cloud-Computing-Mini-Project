from flask import Flask, request, jsonify
from cassandra.cluster import Cluster
import requests
from pprint import pprint
import datetime

cluster = Cluster(['cassandra'])
session = cluster.connect()



app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

app_id = app.config['APP_ID']
app_key = app.config['APP_KEY']


#define main page
@app.route('/', methods=['GET'])
def main_page():
    text = "<html><body>" \
           "<h1>Cloud computing mini-project</h1><h2>Elena Pedrini</h2>" \
           "<br><h4>App Overview:</h4>" \
           "<ul>" \
           "<li><font face='courier'><a href='http://0.0.0.0:8080/status'> /status<a/></font>: " \
                "current status of all tube lines" \
           "<ul><li><font face='courier' color='green'>/status/{tube_line}</font>: " \
                "current status of the tube line specified</li></ul></li>" \
           "<br>" \
           "<li><font face='courier'><a href='http://0.0.0.0:8080/airquality'> /airquality<a/></font>: " \
                "weather forecast for today and tomorrow</li>" \
           "<ul><li><font face='courier' color='green'>/airquality/{day}</font>: " \
                "weather forecast for either the current day " \
                "(<font face='courier'><a href='http://0.0.0.0:8080/airquality/today'>today<a/></font>) " \
                "or the following day " \
                "(<font face='courier'><a href='http://0.0.0.0:8080/airquality/tomorrow'>tomorrow<a/></font>) " \
                "</li></ul></li>" \
           "<br>" \
           "<li><font face='courier' color='green'>/station_info/{station}</font>: basic information of the station specified</li>" \
           "<br>" \
           "<li><font face='courier' color='green'>/journey/{station_from}/{station_to}</font>: " \
                "details about the fastest journey from a station to another one, as specified in the url, " \
                "with information about the journey duration, fare, stops and tube lines to take, " \
                "considering a departure time as of the current time. " \
                "Only the tube is considered as means of transport. The stations parameters are not case sensitive.</li>" \
           "</ul></body></html>"
    return text


#define url template in a function, so that it can be dynamycally built according to the path required by the user
#the url contains app id and app key, stored in a separate file
def build_url(url_section):
    url_template = 'https://api.tfl.gov.uk'+url_section+'app_id={app_id}&app_key={app_key}'
    url = url_template.format(app_id=app_id, app_key=app_key)
    return url


################################################################################################
################################################################################################
#SECTION 1
################################################################################################
#status of tube lines: returns the current status of the tube lines

url_section = '/line/mode/tube/status?' #part of the url to get the information needed from the Tfl API
url_status = build_url(url_section)

@app.route('/status', methods=['GET'])
def get_all_tube_lines_status():
    resp = requests.get(url_status) #get request
    if resp.ok:
        json_resp = resp.json()
        status = [(el["id"], el["lineStatuses"][0]["statusSeverityDescription"]) for el in json_resp]
    else:
        print(resp.reason)
        return resp.reason, 400
    return jsonify(status), 200

@app.route('/status/<tube_line>', methods=['GET'])
def get_single_tube_line_status(tube_line):
    #same as previous function, but for a specific tube line
    resp = requests.get(url_status) #get request
    if resp.ok:
        json_resp = resp.json()
        status = [(el["id"], el["lineStatuses"][0]["statusSeverityDescription"]) for el in json_resp if el["id"]==tube_line] #extract only the information for the tube line specified
        if len(status) == 0:
            status = 'Tube line not found'
    else:
        print(resp.reason)
        return resp.reason, 400
    return jsonify(status), 200



################################################################################################
################################################################################################
#SECTION 2
################################################################################################
#air quality: gets air quality data feed

url_section = '/AirQuality?'
url_airquality = build_url(url_section)

@app.route('/airquality', methods=['GET'])
def get_airquality():
    resp = requests.get(url_airquality)
    if resp.ok:
        json_resp = resp.json()
        #airq = [(el["id"], el["lineStatuses"][0]["statusSeverityDescription"]) for el in json_resp]
        #airq = json_resp["currentForecast"][0]
        airq = [(el["forecastSummary"], el["forecastText"], el["forecastType"]) for el in json_resp["currentForecast"]]
    else:
        print(resp.reason)
        return resp.reason, 400
    return jsonify(airq), 200


@app.route('/airquality/<day>', methods=['GET'])
def get_airquality_daily(day):
    resp = requests.get(url_airquality)
    if resp.ok:
        json_resp = resp.json()
        for el in json_resp["currentForecast"]:
            if day=='today' and el["forecastType"]=='Current':
                airq = (el["forecastSummary"], el["forecastText"])
            elif day=='tomorrow' and el["forecastType"]=='Future':
                airq = (el["forecastSummary"], el["forecastText"])
    else:
        print(resp.reason)
        return resp.reason, 400
    return jsonify(airq), 200



################################################################################################
################################################################################################
#SECTION 3
################################################################################################
#get basic information about a given station

@app.route('/station_info/<station>', methods=['GET'])
def get_station_info(station):
    #search StopPoints by their common name; leading and trailing wildcards are applied automatically
    url_section = '/StopPoint/Search/{station_name}?tflOperatedNationalRailStationsOnly=true&'.format(station_name=station)
                  #the national-rail stations-only flag filters the national rail stations so that only those operated by TfL are returned
    url_station = build_url(url_section)
    resp = requests.get(url_station)
    if resp.ok:
        json_resp = resp.json()
        flag = False
        for el in json_resp["matches"]:
            if station in el["name"].lower() and "tube" in el["modes"] and flag == False: #we force the station to be a tube station to simplify and ignore all the other modes --> otherwise disambiguation problems with other stations given similar names
                station_info = {"icsId": el["icsId"], "modes":el["modes"], "name":el["name"], "zone":el["zone"]}
                flag = True
        if flag == False:
            station_info = 'Station name not found'
            return jsonify(station_info), 404
    else:
        print(resp.reason)
        return resp.reason, 400
    return jsonify(station_info), 200



################################################################################################
################################################################################################
#SECTION 4
################################################################################################
#get the journey planner given two stations id (retrieved in previous section with the get_station_id function)

#first extract station id and name
def get_station_id_and_name(station):
    #search StopPoints by their common name; leading and trailing wildcards are applied automatically
    url_section = '/StopPoint/Search/{station_name}?tflOperatedNationalRailStationsOnly=true&' \
                  .format(station_name=station)
                  #the national-rail stations-only flag filters the national rail stations so that only those operated by TfL are returned
    url_station = build_url(url_section)
    resp = requests.get(url_station)
    if resp.ok:
        json_resp = resp.json()
        flag = False
        for el in json_resp["matches"]:
            if station in el["name"].lower() and "tube" in el["modes"] and flag == False: #we force the station to be a tube station to simplify and ignore all the other modes --> otherwise disambiguation problems with other stations given similar names
                station_id = el["icsId"]
                station_name = el["name"]
                flag = True
        if flag == False:
            station_id = 'Station not found'
            station_name = 'Station not found'
    else:
        print(resp.reason)
    return (station_id, station_name)



@app.route('/journey/<station_from>/<station_to>')
def get_journey_between_2_stations(station_from, station_to):
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    current_time = datetime.datetime.now().strftime("%H%M")

    station_id_from, station_name_from = get_station_id_and_name(station_from)
    station_id_to, station_name_to = get_station_id_and_name(station_to)

    url_section = '/Journey/JourneyResults/{from_st}/to/{to_st}?nationalSearch=false&' \
                  'date={date}&time={time}&journeyPreference=LeastTime&mode=tube&' \
                  .format(from_st=station_id_from, to_st=station_id_to, date=current_date, time=current_time)
             #"nationalSearch=false" means the journey does not cover stops outside London
             #"leasttime" = the journey preference --> possible options: "leastinterchange" | "leasttime" | "leastwalking"
             #"tube" = the mode; it can be comma separated list of modes (eg "tube,dlr,bus,train")
    url_journey = build_url(url_section)
    resp = requests.get(url_journey)

    if resp.ok:
        json_resp = resp.json()
        flag = False

        min_journey_duration = 120 #max amount of time arbitrarily chosen for a single journey
        for journey in json_resp["journeys"]:
            if int(journey["duration"]) < min_journey_duration:
                min_journey_duration = int(journey["duration"])
        if min_journey_duration == 120:
            result = 'No journey option found with a max duration of 120 minutes'
        else:
            result = []
            flag2 = False
            for journey in json_resp["journeys"]:
                #selecting the appropriate fields of the long json file returned from the api call
                fastest_journey = {}
                if int(journey["duration"]) == min_journey_duration and flag2 == False and "fare" in journey:
                    fastest_journey["from"] = station_name_from
                    fastest_journey["to"] = station_name_to
                    fastest_journey["journey_duration"] = journey["duration"]
                    fastest_journey["total_fare"] = journey["fare"]["totalCost"]
                    fastest_journey["stop_points"] = []
                    fastest_journey["tube_line"] = []
                    for el in journey["legs"]:
                        for stop in el["path"]["stopPoints"]:
                            fastest_journey["stop_points"].append(stop["name"])
                        if el["routeOptions"][0]["name"]!="":
                            fastest_journey["tube_line"].append( el["routeOptions"][0]["name"] )
                    flag = True
                    flag2 = True
                if len(fastest_journey)!=0:
                    result.append(fastest_journey)

            if flag==False:
                result = 'No journey found with the specified criteria'
                return jsonify(result), 404

    else:
        print(resp.reason)
        return resp.reason, 400
    return jsonify(result), 200




################################################################################################
################################################################################################
#SECTION 5
################################################################################################
#test connection with cassandra cluster

@app.route('/test_db/<station>')
def profile(station):
   query = session.execute("""select * from stations.nodes_dimension where Station = '{}'""".format(station))
   if query!="":
        return jsonify(query)
   else:
        return "Station not found"



################################################################################################
################################################################################################
#MAIN
################################################################################################
if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 8080)
