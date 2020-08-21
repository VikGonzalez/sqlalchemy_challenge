# DEPENDENCIES
import sqlalchemy
import numpy as np
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

# DATABASE
#start engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect into new model
Base = automap_base()

# reflect tables
Base.prepare(engine, reflect= True)

# save tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# FLASK
app = Flask(__name__)
app.config["JSON_SORT_KEYS"]=False

# routes
@app.route("/")
def welcome():
    return (
        f"<b>Available Routes:</b><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<b>The following routes are also available, with specified start and end dates formatted as YYYY-MM-DD:</b><br/>"
        f"/api/v1.0/(start)<br/>"
        f"/api/v1.0/(start)/(end)<br/>"
    )

# API
@app.route("/api/v1.0/precipitation")
def precipitation():

    
    session = Session(engine)

    results = (
        session.query(Measurement.date, Measurement.station, Measurement.prcp)
        .group_by(Measurement.date, Measurement.station)
        .all()
    )

    session.close()

    # initialize list
    prcp_list = []
    d_o = ''

    # Dictionary
    for date, station, prcp in results: 
            prcp_dict = {}
            if date != d_o:
                prcp_dict["date"] = date
            p_dict = {}
            p_dict[station] = prcp
            prcp_dict["prcp"]= p_dict
            prcp_list.append(prcp_dict)
            d_o = date

    return jsonify(prcp_list)


# Weather API
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = (
        session.query(Station.station, Station.name, Station.longitude, Station.latitude, Station.elevation)
        .all()
    )

    session.close()

    st_list = []
    for station, name,longitude, latitude, elevation in results: 
            st_dict = {}
            st_dict["station"] = station
            st_dict["name"]= name
            st_dict["geo"]= {"lng":longitude,"lat":latitude,"elev":elevation}
            st_list.append(st_dict)

    return jsonify(st_list)

# temperatures 
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    activeStation = ( 
            session
            .query(Measurement.station, Station.name, func.count(Measurement.station))
            .group_by(Measurement.station)
            .join(Station, Measurement.station == Station.station)
            .order_by(func.count(Measurement.station).desc())
            .first()
            )

    stationLast = (
    session
    .query(Measurement.date)
    .filter_by(station = activeStation[0])
    .order_by(Measurement.date.desc())
    .first()
    ._asdict()
    )

    stationLast_f = dt.datetime.strptime(stationLast['date'],'%Y-%m-%d')
    stationStart = dt.date(stationLast_f.year -1,stationLast_f.month, stationLast_f.day)

    activeStationData = (
                session
                .query(Measurement.date, Measurement.tobs)
                .filter_by(station = activeStation[0])
                .filter(Measurement.date >= stationStart)
                .filter(Measurement.date <= stationLast['date'])
                .order_by(Measurement.date.asc())
                .all()
                )

    session.close()

    tobs_list = []
    for date, tobs in activeStationData: 
            tobs_dict = {}
            tobs_dict["date"] = date
            tobs_dict["tobs"]= tobs
            tobs_list.append(tobs_dict)

# Start Date
@app.route("/api/v1.0/<start>")
def tobs_start(start):


            session = Session(engine)

            activeStation = ( 
                session
                .query(Measurement.station, Station.name, func.count(Measurement.station))
                .group_by(Measurement.station)
                .join(Station, Measurement.station == Station.station)
                .order_by(func.count(Measurement.station).desc())
                .first()
                )

            activeStationData = (
                        session
                        .query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))
                        .filter_by(station = activeStation[0])
                        .filter(Measurement.date >= start)
                        .all()
                        )

            session.close()

            tobs_list = []
            tobs_dict = {}
            tobs_dict["TMIN"] = activeStationData[0][0]
            tobs_dict["TMAX"]= activeStationData[0][1]
            tobs_dict["TAVG"] = round(activeStationData[0][2],2)
            tobs_list.append(tobs_dict)

#Start/ End Date
@app.route("/api/v1.0/<start>/<end>")
def tobs_start_end(start,end):
    activeStation = ( 
            session
            .query(Measurement.station, Station.name, func.count(Measurement.station))
            .group_by(Measurement.station)
            .join(Station, Measurement.station == Station.station)
            .order_by(func.count(Measurement.station).desc())
            .first()
            )

    activeStationData = (
                session
                .query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))
                .filter_by(station = activeStation[0])
                .filter(Measurement.date >= start)
                .filter(Measurement.date <= end)
                .all()
                )

    session.close()

    tobs_list = []
    tobs_dict = {}
    tobs_dict["TMIN"] = activeStationData[0][0]
    tobs_dict["TMAX"]= activeStationData[0][1]
    tobs_dict["TAVG"] = round(activeStationData[0][2],2)
    tobs_list.append(tobs_dict)

    return jsonify(tobs_list)

# Execute API
if __name__ == '__main__':
    app.run(debug=True)