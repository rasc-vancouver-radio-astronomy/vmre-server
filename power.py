import datetime
import json
import os
from multiprocessing import Pool

import numpy as np

import config

def power(db):

    datafiles = get_files(db)

    with Pool(None) as p:
        rr = p.map(power_file, datafiles)

    for r in rr:
        iq_filename = r[0]
        power_filename = r[1]
        db["files"][iq_filename]["power"] = power_filename

def get_files(db):

    datafiles = []
    for station_id, station in config.stations.items():
        for filename in sorted(os.listdir(station["data_path"])):

            if os.path.splitext(filename)[1] != ".json":
                continue

            base_filename = os.path.splitext(f"{station['data_path']}/{filename}")[0]
            json_filename = base_filename + ".json"
            iq_filename = base_filename + ".dat"

            if not os.path.exists(iq_filename):
                print(f"{iq_filename} is missing!")
                continue

            #print(f"Reading {json_filename}...")
            try:
                params = json.load(open(json_filename, "r"))
            except:
                print(f"{json_filename} has JSON parse error!")
                continue
            datetime_started = datetime.datetime.strptime(params["datetime_started"], config.time_format_data)
            today = datetime.datetime.now()
            td = today - datetime_started
            if td.days > config.analyze_days:
                #print(f"Skipping {iq_filename} because it's older than {config.analyze_days} days.")
                continue
            
            if iq_filename not in db["files"]:
                db["files"][iq_filename] = {"size": 0}

            db["files"][iq_filename]["params"] = params
            db["files"][iq_filename]["station_id"] = station_id
            db["files"][iq_filename]["datetime_readable"] = datetime_started.strftime(config.time_format_readable)

            datafiles.append({
                "json": json_filename,
                "iq": iq_filename,
                "base": base_filename,
                "params": params,
                "datetime_started": datetime_started,
                "size": db["files"][iq_filename]["size"],
                "station_id": station_id,
            })

            db["files"][iq_filename]["size"] = os.path.getsize(iq_filename)

    return datafiles

def power_file(datafile):

    iq_filename = datafile["iq"]
    base_filename = datafile["base"]
    params = datafile["params"]
    station_id = datafile["station_id"]
    csv_filename = f"power/power_station{station_id}_{os.path.split(base_filename)[1]}.csv"

    if os.path.exists(csv_filename) and os.path.getmtime(iq_filename) < os.path.getmtime(csv_filename):
        return (iq_filename, csv_filename)

    # Extract parameters.
    bw = params["bandwidth"]

    print(f"Analyzing {iq_filename}.")

    dt = config.dt
    n = config.n

    index_dt = int(dt*bw)
    iq_len = os.path.getsize(iq_filename) // 8

    power = np.zeros(int(iq_len // index_dt))
    f = open(iq_filename, "rb")

    for i in range(int(iq_len//index_dt)):

        f.seek(i*index_dt*8)

        # Load a chunk of the data for processing.
        iq_slice = np.fromfile(f, np.complex64, count=index_dt)
        iq_slice = iq_slice - np.mean(iq_slice)

        # Find the spectrum of the chunk.
        fft = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq_slice, n=n))))

        trim = n // 16
        fft = fft[trim:len(fft)-trim]

        blank = config.notch_bw/bw*len(fft)
        for j in range(int(len(fft)/2-blank/2), int(len(fft)/2+blank/2)):
            fft[j] = -np.Inf

        power[i] = (max(fft) - np.median(fft))

    with open(csv_filename, "w") as f:
        for i, p in enumerate(power):
            f.write(f"{i*dt},{p}\n")

    return (iq_filename, csv_filename)
