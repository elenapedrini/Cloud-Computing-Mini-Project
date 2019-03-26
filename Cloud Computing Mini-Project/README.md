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
