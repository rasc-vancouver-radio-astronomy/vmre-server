import datetime
import math
import os

import colorcet as cc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import config

def plot(db):

    os.makedirs("site", exist_ok=True)

    plt.style.use("dark_background")

    for event_id, event in enumerate(db["events"]):

        if "plots" in event or event["interference"]:
            continue

        print(f"Plotting event ID {event_id} ({event['file_path']}:{event['file_index']}).")

        event["plots"] = {}

        file = db["files"][event["file_path"]]
        params = file["params"]

        bw = params["bandwidth"]

        i = event["file_index"]
        dt = config.dt

        iq_len = os.path.getsize(event["file_path"]) // 8

        index_t0 = int(i*dt*bw - 15*bw)
        if index_t0 < 0:
            index_t0 = 0

        index_t1 = int(i*dt*bw + 15*bw)
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
            Pxx, freqs, bins, im = plt.specgram(iq_slice, NFFT=NFFT, Fs=bw, noverlap=NFFT/2, cmap=cc.cm.bmw, xextent=(-15, 15))

            plt.ylabel("Doppler shift (Hz)")
            plt.xlabel("Time (sec)")
            plt.title(event['datetime_readable'])

            vmin = -110
            vmax = -90
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
