import datetime
import math
import os
import sys

import colorcet as cc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import config

from multiprocessing import Pool

def plot(db):

    plots = []

    for event_id, event in enumerate(db["events"]):
        
        if event["interference"]:
            continue

        if "recreate_plots" not in sys.argv:
            if "plots" in event and event["plots"]:
                continue

        event_time = datetime.datetime.strptime(event["datetime_str"], "%Y-%m-%d_%H-%M-%S.%f")

        for file_path, file in db["files"].items():

            # Check if station has any data for this event
            start = datetime.datetime.strptime(file["params"]["datetime_started"], "%Y-%m-%d_%H-%M-%S.%f")
            file_duration = file["size"] / file["params"]["bandwidth"] / 8
            end = start + datetime.timedelta(seconds=file_duration)
            if event_time < start or event_time > end:
                continue
            
            # Check if station was tuned to the right frequency
            if file["params"]["center_frequency"] != event["center_frequency"]:
                continue

            event["stations_online"].append(file["params"]["station_id"])

            start_idx = int(((event_time-start).total_seconds() + config.spec_start) * file["params"]["bandwidth"])
            start_t = config.spec_start
            if start_idx < 0:
                start_idx = 0
                start_t = 0
            end_idx = int(((event_time-start).total_seconds() + config.spec_end) * file["params"]["bandwidth"])
            end_t = config.spec_end
            if end_idx >= file["size"]//8:
                end_idx = file["size"]//8

            plots.append({
                "file_path": file_path,
                "file": file,
                "start_idx": start_idx,
                "start_t": start_t,
                "end_idx": end_idx,
                "event": event,
                "event_id": event_id,
            })

    with Pool(None) as p:
        new_plots = p.map(plot_event, plots)
    
    for i, p in enumerate(plots):
        db["events"][plots[i]["event_id"]]["plots"] += new_plots[i]


def plot_event(p):

    file_path = p["file_path"]
    file = p["file"]
    start_idx = p["start_idx"]
    start_t = p["start_t"]
    end_idx = p["end_idx"]
    event = p["event"]
    event_id = p["event_id"]
    
    plt.style.use("dark_background")

    print(f"Plotting event ID {event_id} ({file_path}:{start_idx}:{end_idx}).")

    plots = {}

    params = file["params"]

    bw = params["bandwidth"]

    dt = config.dt

    f = open(file_path, "rb")
    f.seek(start_idx*8)
    iq_slice = np.fromfile(f, np.complex64, count=end_idx-start_idx)
    iq_slice = iq_slice - np.mean(iq_slice)

    plots = []

    for NFFT in config.NFFTs:

        plt.figure(figsize=(7*len(iq_slice)/bw/(config.spec_end-config.spec_start),6))
        Pxx, freqs, bins, im = plt.specgram(iq_slice, NFFT=NFFT, Fs=bw, noverlap=NFFT/2, cmap=cc.cm.bmw, xextent=(start_t, start_t+len(iq_slice)/bw))

        plt.ylabel("Doppler shift (Hz)")
        plt.xlabel("Time (sec)")
        plt.title(f"VMRE event {event_id} station {file['station_id']} {event['center_frequency']/1E6:.3f} MHz {event['datetime_readable']}")

        bottom, top = plt.ylim()
        plt.ylim((bottom+params["transition_width"], top-params["transition_width"]))

        cb = plt.colorbar()
        cb.remove()

        vmin = 10 * np.log10(np.median(Pxx))
        vmax = 10 * np.log10(np.max(Pxx))
        im.set_clim(vmin=vmin, vmax=vmax)

        plot_path = f"site/event{event_id}_{event['datetime_str']}_{event['center_frequency']/1E6:.3f}MHz_station{file['station_id']}_FFT{NFFT}.png"

        #plt.colorbar(im).set_label("Power (dB)")
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()

        plots.append(plot_path)

    return plots

def plot_power(db):

    # WIP

    for day_num in range(config.analyze_days):

        # Ugly...
        today = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d")
        tomorrow = today + datetime.timedelta(seconds=24*60*60)

        power = {}

        for filename in db["files"]:

            file = db["files"][filename]
            params = file["params"]

            datetime_started = datetime.datetime.strptime(params["datetime_started"], "%Y-%m-%d_%H-%M-%S.%f")
            datetime_finished = datetime_started + datetime.timedelta(seconds=file["size"]//params["bandwidth"]//8)

            # if datetime_started < tomorrow and datetime_finished > today:

                # power[params["station_id"]] = np.zeros(24*60*60)
