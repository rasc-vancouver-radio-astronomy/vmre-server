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

def plot(db):

    plt.style.use("dark_background")

    summary_events = []

    for event in db["events"]:

        event_id = event["id"]

        if event["interference"]:
            continue

        summary_events.append(event)

        if "recreate_plots" not in sys.argv:
            if "plots" in event:
                continue

        print(f"Plotting event ID {event_id} ({event['file_path']}:{event['file_index']}).")

        event["plots"] = {}

        file = db["files"][event["file_path"]]
        params = file["params"]

        bw = params["bandwidth"]

        i = event["file_index"]
        dt = config.dt

        iq_len = os.path.getsize(event["file_path"]) // 8

        index_t0 = int(i*dt*bw - 5*bw)
        if index_t0 < 0:
            index_t0 = 0

        index_t1 = int(i*dt*bw + 25*bw)
        if index_t1 > iq_len:
            index_t1 = iq_len

        t0 = index_t0 * dt
        t1 = index_t1 * dt

        f = open(event["file_path"], "rb")
        f.seek(index_t0*8)
        iq_slice = np.fromfile(f, np.complex64, count=index_t1-index_t0)
        iq_slice = iq_slice - np.mean(iq_slice)

        for NFFT in config.NFFTs:

            plt.figure(figsize=(10,8))
            Pxx, freqs, bins, im = plt.specgram(iq_slice, NFFT=NFFT, Fs=bw, noverlap=NFFT/2, cmap=cc.cm.bmw, xextent=(-config.spec_start, config.spec_width-config.spec_start))

            plt.ylabel("Doppler shift (Hz)")
            plt.xlabel("Time (sec)")
            plt.title(f"VMRE event {event_id} {event['datetime_readable']}")

            vmin = 10 * np.log10(np.median(Pxx))
            vmax = 10 * np.log10(np.max(Pxx))
            im.set_clim(vmin=vmin, vmax=vmax)

            plot_path = f"site/event{event_id}_{event['datetime_str']}_FFT{NFFT}.png"

            plt.colorbar(im).set_label("Power (dB)")
            plt.savefig(plot_path)
            plt.close()

            if "spectrum" not in event["plots"]:
                event["plots"]["spectrum"] = {}

            event["plots"]["spectrum"][NFFT] = {
                "path": plot_path
            }

    plt.figure(figsize=(10,6))
    plt.ylabel("Number of events")
    plt.xlabel("Date")
    x = []
    y = []
    for i in range(config.analyze_days):
        x.append((datetime.datetime.now() - datetime.timedelta(days=i+1)).strftime("%m-%d"))
        y.append(0)
    for event in summary_events:
        date_str = datetime.datetime.strptime(event["datetime_str"], "%Y-%m-%d_%H-%M-%S").strftime("%m-%d")
        if date_str in x:
            day = x.index(date_str)
            y[day] += 1
    x.reverse()
    y.reverse()
    plt.bar(range(len(x)), y, align="center")
    plt.xticks(range(len(x)), x)
    plt.title(f"Detected events over the past {config.analyze_days} days")
    plt.savefig(f"site/summary.png", bbox_inches='tight')
    plt.close()
