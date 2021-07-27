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
        
        event_time = datetime.datetime.strptime(event["datetime_str"], config.time_format)

        for file_path, file in db["files"].items():

            # Check if station has any data for this event
            start = datetime.datetime.strptime(file["params"]["datetime_started"], config.time_format_data)
            file_duration = file["size"] / file["params"]["bandwidth"] / 8
            end = start + datetime.timedelta(seconds=file_duration)
            if event_time < start or event_time > end:
                continue
            
            # Check if station was tuned to the right frequency
            if file["params"]["center_frequency"] != event["center_frequency"]:
                continue

            if "stations_online" not in event:
                event["stations_online"] = []
            event["stations_online"].append(file["params"]["station_id"])

            if "plots" not in event:
                event["plots"] = []

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

    # Generate 'daily detections' chart. Create y-axis first
    events_per_day = [0] * (config.analyze_days)
    for e in db['events']:
        if len(e["stations"]) > 1:
            today = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y%m%d"), "%Y%m%d")
            event_time = datetime.datetime.strptime(datetime.datetime.strptime(e["datetime_str"], config.time_format).strftime("%Y%m%d"), "%Y%m%d")
            day_delta = (today - event_time).days
            if day_delta < config.analyze_days:
                events_per_day[day_delta] += 1
    events_per_day.reverse()

    # Create x-axis for 'daily detections' chart
    x = []
    for i in range(config.analyze_days):
        x.append( (datetime.datetime.today() - datetime.timedelta(i)).strftime("%m-%d") )
    x.reverse()

    plt.style.use('dark_background')
    fig, ax = plt.subplots()
    plt.bar(x, events_per_day)
    # plt.xticks(rotation=90)
    plt.title('VMRE Daily Detections Chart')
    plt.xlabel('Date (MM-DD)')
    plt.ylabel('Number of Confirmed Events')
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig("plots/daily.png")
    plt.close()


def plot_event(p):

    file_path = p["file_path"]
    file = p["file"]
    start_idx = p["start_idx"]
    start_t = p["start_t"]
    end_idx = p["end_idx"]
    event = p["event"]
    event_id = p["event_id"]
    
    plt.style.use("dark_background")

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

        plot_path = f"plots/{event['datetime_str']}_{event['center_frequency']/1E6:.3f}MHz_station{file['station_id']}_FFT{NFFT}.png"
        plots.append(plot_path)

        if os.path.exists(plot_path) and os.path.getmtime(file_path) < os.path.getmtime(plot_path):
            continue

        print(f"Plotting event {event_id} NFFT={NFFT} ({file_path}:{start_idx}:{end_idx}).")

        plt.figure(figsize=(7*len(iq_slice)/bw/(config.spec_end-config.spec_start),6))
        Pxx, freqs, bins, im = plt.specgram(iq_slice, NFFT=NFFT, Fs=bw, noverlap=NFFT/2, cmap=cc.cm.bmw, xextent=(start_t, start_t+len(iq_slice)/bw))

        plt.ylabel("Doppler shift (Hz)")
        plt.xlabel("Time (sec)")
        plt.title(f"VMRE event (station {file['station_id']} {event['center_frequency']/1E6:.3f} MHz {event['datetime_readable']})")

        bottom, top = plt.ylim()
        plt.ylim((bottom+params["transition_width"], top-params["transition_width"]))

        cb = plt.colorbar()
        cb.remove()

        vmin = 10 * np.log10(np.median(Pxx))
        vmax = 10 * np.log10(np.max(Pxx))
        im.set_clim(vmin=vmin, vmax=vmax)

        #plt.colorbar(im).set_label("Power (dB)")
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()

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
