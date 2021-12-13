import datetime as dt
import os
from multiprocessing import Pool
import json

import colorcet as cc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.stats.stats import pearsonr

import config as cfg

def detect(db):

    # Find the start and end datetimes for each file
    for station in cfg.stations.values():
        for filename in os.listdir(station["data_path"]):

            if os.path.splitext(filename)[1] != ".json":
                continue

            base_filename = os.path.splitext(f"{station['data_path']}/{filename}")[0]
            json_filename = base_filename + ".json"
            iq_filename = base_filename + ".dat"

            if not os.path.exists(iq_filename):
                print(f"{iq_filename} is missing!")
                continue

            file_size = os.path.getsize(iq_filename)

            if file_size == 0:
                print(f"{iq_filename} has size 0!")
                continue

            if file_size < 400000:
                print(f"{iq_filename} is too small! size {file_size}")
                continue

            try:
                params = json.load(open(json_filename, "r"))
            except:
                print(f"{json_filename} has JSON parse error!")
                continue

            if "bandwidth" not in params or "datetime_started" not in params or "center_frequency" not in params:
                print(f"{json_filename} is missing parameters!")
                continue

            datetime_started = dt.datetime.strptime(params["datetime_started"], cfg.time_format_data)

            today = dt.datetime.now()
            td = today - datetime_started
            if td.days > cfg.analyze_days:
                continue

            datetime_ended = datetime_started + dt.timedelta(seconds=(file_size//8)/params["bandwidth"])
            print(f"file starts {datetime_started} and ends {datetime_ended}")

            db["files"].append({
                "filename": iq_filename,
                "start": datetime_started,
                "end": datetime_ended,
                "bandwidth": params["bandwidth"],
                "frequency": params["center_frequency"],
                "station_id": params["station_id"],
                "params": params,
                "size": file_size
            })

    # Starting with analyze_days ago
    today = dt.datetime.strptime(dt.datetime.now().strftime("%Y%m%d"), "%Y%m%d")
    t0 = today - dt.timedelta(days=cfg.analyze_days) + dt.timedelta(days=1)

    db["events"] = []

    # For every dt second time period
    for i in range(200, cfg.analyze_days * 24*60*60 // cfg.dt):

        t = t0 + dt.timedelta(seconds=i*cfg.dt)
        t_end = t + dt.timedelta(seconds=cfg.dt)

        # Check which files have complete data for this period
        t_datafiles = []
        for datafile in db["files"]:
            if t > datafile["start"] and t_end < datafile["end"]:
                t_datafiles.append(datafile)

        t_P = []
        # For each file
        for datafile in t_datafiles:
            
            datafile_idx = int((t - datafile["start"]).total_seconds() * datafile["bandwidth"])

            # Load the data
            iq_slice = np.fromfile(datafile["filename"], np.complex64, offset=datafile_idx*8, count=cfg.dt*datafile["bandwidth"])

            # Correct DC
            iq_slice = iq_slice - np.mean(iq_slice)

            # Calculate the spectrogram
            Pxx, freqs, bins, im = plt.specgram(
                iq_slice,
                NFFT=cfg.n,
                Fs=datafile["bandwidth"],
                noverlap=cfg.n/2
            )
            plt.clf()
            plt.close()

            t_P.append(np.log10(Pxx) / np.median(np.log10(Pxx)))

        for j in range(len(t_P)):
            # Calculate standard deviation
            t_std = np.std(t_P[j])
            t_thr = np.median(t_P[j]) + t_std*cfg.sig
            # Apply clipping
            t_P[j] = np.clip(t_P[j] - t_thr, 0, None)

        t_P = np.asarray(t_P)

        # Sum the spectrograms together
        t_P = np.prod(t_P**(1/len(t_P)), axis=0)

        # Calculate energy
        # E = 10*np.log10(np.sum(t_P))
        E = np.sum(t_P)

        print(f"t={t} {len(t_datafiles)=} {E=}")

        # Threshold
        if E >= cfg.thr:
            db["events"].append({
                "datetime_str": dt.datetime.strftime(t, cfg.time_format),
                "datetime_readable": dt.datetime.strftime(t, cfg.time_format_readable),
                "energy": E,
            })
            print("Event!")
