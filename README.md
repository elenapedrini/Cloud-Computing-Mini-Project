# CLOUD COMPUTING MINI-PROJECT

About
-----
The goal of the mini-project is to apply and extend the techniques practised in the module of Cloud Computing attended at Queen Mary University of London, in order to build a prototype of a Cloud application.

The application is developed in Python and Flask, a web framework implemented in Python useful for creating web applications. 


Main features
-----
The mini project is mainly focused on the following aspects of Cloud applications:

- REST-based service interface
- interaction with external REST services
- use of on an external Cloud database for persisting information
- support for cloud scalability, deployment in a container environment
- Cloud security awareness


Domain
------
The application uses the [Tfl REST API](https://api.tfl.gov.uk/) to provide some information about the current status of tube lines, the weather forecast for the current and the following day, the details of the journey arbitrarily defined between two given stations, and more. 


App Overview
------

- /status: current status of all tube lines
  /status/{tube_line}: current status of the tube line specified

- /airquality: weather forecast for today and tomorrow
  /airquality/{day}: weather forecast for either the current day (today) or the following day (tomorrow)

- /station_info/{station}: basic information of the station specified

- /journey/{station_from}/{station_to}: details about the fastest journey from a station to another one, as specified in the url, with information about the journey duration, fare, stops and tube lines to take, considering a departure time as of the current time. Only the tube is considered as means of transport. The stations parameters are not case sensitive.


Set up
-------
#### Deployment
Configure the compute zone and the project ID for reference in later commands:
```bash
gcloud config set compute/zone us-central1-b
export PROJECT_ID="$(gcloud config get-value project -q)"
```

Create a Kubernetes cluster (with 4 nodes in this case):
```bash
gcloud container clusters create cassandra --num-nodes=4 --machine-type "n1-standard-2"
```

Define a Cassandra service and run the three components: 
```bash
kubectl create -f cassandra-peer-service.yml
kubectl create -f cassandra-service.yml
kubectl create -f cassandra-replication-controller.yml
```

Scale up the number of nodes (via the replication-controller:
```bash
kubectl scale rc cassandra --replicas=2
```


#### Loading data to the Cassandra cluster
Copy the data into the Cassandra cluster:
```bash
kubectl cp data/StationNodesDescription.csv cassandra-pflfz:/StationNodesDescription.csv
kubectl cp data/StationPassengerLinkFlows.csv cassandra-pflfz:/StationPassengerLinkFlows.csv
```
Build the keyspace and the table hosting the data:
```bash
kubectl exec -it cassandra-pflfz cqlsh

CREATE KEYSPACE stations WITH REPLICATION = {'class':'SimpleStrategy', 'replication_factor':2};

CREATE TABLE stations.nodes_dimension (
Node int PRIMARY KEY,
Station text,
Node_Type text, 
Line_Direction text,
Platform_Direction text, 
Line text,
Platform_Type text, 
Destination text,
Station_Entrance_Exit text,
NLC int,
NAPTAN text,
Deprecated Boolean,
Year_of_addition text
);
```
Populate the created table with the data from the csv file:
```bash
COPY stations.nodes_dimension (   
 Node,
 Station,
  Node_Type, 
  Line_Direction,
  Platform_Direction, 
  Line,
  Platform_Type, 
  Destination,
  Station_Entrance_Exit,
  NLC,
  NAPTAN,
  Deprecated,
  Year_of_addition
  )
FROM 'StationNodesDescription.csv' WITH HEADER=TRUE AND DELIMITER=',';
```

#### Run the app
Create the docker image and push it to the Google Cloud repository:
 ```bash
 docker build -t gcr.io/${PROJECT_ID}/mini-project-app:v1 .
 docker push gcr.io/${PROJECT_ID}/mini-project-app:v1
 ```
 
Run the image as a service exposing the deployment to get an external IP address, using the .yml files:
 ```bash
kubectl create -f app_deployment.yml
kubectl create -f load_balancer.yml
 ```
 
 
 Further work
 -------
 There are many areas in which the application can be improved. For example:
 - the front-end can be transformed into a more user-friendly interface;
 - the matching between the external parameters given interactively by the user about the tube stations names and the actual stations names needs to be carried on in refining wildcards and pattern-matching conditions, for example by implementing autofill suggestions which allow the users to have a better experience while using the app, without asking them to type long names in the url (e.g. King's Cross St. Pancras).
