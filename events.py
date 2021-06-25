import datetime
import json
import os
from multiprocessing import Pool

import numpy as np

import config


def events(db):

    e = []
    db["events"] = []

    with Pool(None) as p:
        rr = p.map(events_file, db["files"].items())

    for r in rr:
        csv = open(r, "r")
        for line in csv.readlines():
            fields = line.strip().split(",")
            e.append({
                "stations": [fields[1]],
                "datetime_str": fields[0],
                "center_frequency": float(fields[2]),
                "datetime_readable": datetime.datetime.strftime(datetime.datetime.strptime(fields[0], config.time_format), config.time_format_readable),
            })

    # Ignore any events too close to each other
    dates = {}
    for event in e:
        dupe = False
        for d in dates:
            if abs(d - int(event["datetime_str"])) < (config.spec_end-config.spec_start)*1E6:
                dupe = True
                break

        if not dupe:
            db["events"].append(event.copy())
            dates[int(event["datetime_str"])] = len(db["events"])-1
        else:
            for s_id in event["stations"]:
                if s_id not in db["events"][dates[d]]["stations"]:
                    db["events"][dates[d]]["stations"].append(s_id)
    
def events_file(f):
    file = f[1]
    iq_filename = f[0]
    base_filename = os.path.splitext(iq_filename)[0]
    csv_filename = f"events/events_station{file['station_id']}_{os.path.split(base_filename)[1]}.csv"

    if os.path.exists(csv_filename) and os.path.getmtime(iq_filename) < os.path.getmtime(csv_filename):
        return csv_filename

    power = np.genfromtxt(file["power"], delimiter=",")[:,1]
    events = []

    dt = config.dt
    datetime_started = datetime.datetime.strptime(file["params"]["datetime_started"], "%Y-%m-%d_%H-%M-%S.%f")

    # Author: William Wall

    wrsig = 100
    sn_thr = config.power_threshold

    rmean = power - power
    rsig = power - power
    rmed = power - power

    for ii in range(len(power)):
        bi = ii-wrsig
        if bi < 0:
            bi = 0
        ei = ii+wrsig+1
        if ei > len(power):
            ei = len(power)
        rmean[ii] = np.mean(power[bi:ei])
        rsig[ii] = np.std(power[bi:ei])
        rmed[ii] = np.median(power[bi:ei])

    thresh = rmean + sn_thr*rsig
    rdat = 1.*power
    loc_thr = power > thresh
    rdat[loc_thr] = rmed[loc_thr]
    num_pk = len(np.where(loc_thr)[0])
    num_pks = 1*num_pk

    counter = 0
    while num_pks != 0:
        counter = counter + 1
        for ii in range(len(rdat)):
            bi = ii-wrsig
            if bi < 0:
                bi = 0
            ei = ii+wrsig+1
            if ei > len(rdat):
                ei = len(rdat)
            rmean[ii] = np.mean(rdat[bi:ei])
            rsig[ii] = np.std(rdat[bi:ei])
            rmed[ii] = np.median(rdat[bi:ei])
        thresh = rmean + sn_thr*rsig
        loc_thr = rdat > thresh
        rdat[loc_thr] = rmed[loc_thr]
        num_pks = len(np.where(loc_thr)[0])

    ind = np.where(power > thresh)[0].tolist()

    # End of William's code.

    print(f"Found {len(ind)} events in {file['power']}.")

    f = open(csv_filename, "w")

    for i in ind:
        datetime_event = datetime_started + datetime.timedelta(seconds=i*dt)
        f.write(f"{datetime_event.strftime(config.time_format)},{file['station_id']},{file['params']['center_frequency']}\n")
    
    return csv_filename
