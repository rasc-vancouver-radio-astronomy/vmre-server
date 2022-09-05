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
import scipy

import config as cfg

from multiprocessing import Pool

def plot(db, files):

    plots = []

    for event in db["events"]:
        
        event_time = datetime.datetime.strptime(event["datetime_str"], cfg.time_format)

        for file in files:

            # Check if file has any data for this event
            if event_time < file["start"] or event_time > file["end"]:
                continue
            
            if "stations_online" not in event:
                event["stations_online"] = []
            event["stations_online"].append(file["params"]["station_id"])

            if "plots" not in event:
                event["plots"] = []

            start_idx = int(((event_time-file["start"]).total_seconds()) * file["params"]["bandwidth"])
            start_t = 0
            if start_idx < 0:
                start_idx = 0
                start_t = 0
            end_idx = int(((event_time-file["start"]).total_seconds() + cfg.dt) * file["params"]["bandwidth"])
            if end_idx >= file["size"]//8:
                end_idx = file["size"]//8

            plots.append({
                "file": file,
                "start_idx": start_idx,
                "start_t": start_t,
                "end_idx": end_idx,
                "event": event,
            })

    with Pool(None) as p:
        new_plots = p.map(plot_event, plots)
    
    for i, p in enumerate(plots):
        p["event"]["plots"] += new_plots[i]

    # # Generate 'daily detections' chart. Create y-axis first
    # events_per_day = []
    # for i in range(len(cfg.stations)):
    #     events_per_day.append([0] * (cfg.daily_detections_plot_days))
    # for e in db['events'].values():
    #     today = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y%m%d"), "%Y%m%d")
    #     event_time = datetime.datetime.strptime(datetime.datetime.strptime(e["datetime_str"], cfg.time_format).strftime("%Y%m%d"), "%Y%m%d")
    #     day_delta = (today - event_time).days
    #     if day_delta < cfg.daily_detections_plot_days:
    #         for i in range(e['observations']):
    #             events_per_day[i][day_delta] += 1
    # for i in range(len(cfg.stations)):
    #     events_per_day[i].reverse()

    # # Create x-axis for 'daily detections' chart
    # x = []
    # for i in range(cfg.daily_detections_plot_days):
    #     x.append( (datetime.datetime.today() - datetime.timedelta(i)).strftime("%m-%d") )
    # x.reverse()

    # plt.style.use('dark_background')
    # fig, ax = plt.subplots()
    # fig.set_figheight(5)
    # fig.set_figwidth(15)
    # for i in range(0, len(cfg.stations)):
    #     plt.bar(x, events_per_day[i], label=f"{i+1} Observations")
    # # plt.xticks(rotation=90)
    # plt.legend()
    # plt.title('VMRE Daily Detections Chart')
    # plt.xlabel('Date (MM-DD)')
    # plt.ylabel('Number of Detections')
    # fig.autofmt_xdate()
    # plt.xticks(fontsize=9, rotation=90, ha='center')
    # plt.tight_layout()
    # plt.savefig(f"{cfg.html_path}/daily.png")
    # plt.close()

    # # Create time-of-day chart
    # hours = []
    # for i in range(len(cfg.stations)):
    #     hours.append([0]*24)
    # for e in db['events'].values():
    #     event_time = datetime.datetime.strptime(e["datetime_str"], cfg.time_format)
    #     hour = event_time.hour
    #     for i in range(e["observations"]):
    #         hours[i][hour] += 1
    # plt.style.use('dark_background')
    # for i in range(0, len(cfg.stations)):
    #     plt.bar(range(24), hours[i], label=f"{i+1} Observations")
    # plt.legend()
    # plt.title('VMRE Time-of-Day Chart')
    # plt.xlabel('Hour')
    # plt.ylabel('Number of Detections')
    # plt.tight_layout()
    # plt.savefig(f"{cfg.html_path}/timeofday.png")
    # plt.close()

def plot_event(p):

    file = p["file"]
    file_path = file["filename"]
    start_idx = p["start_idx"]
    start_t = p["start_t"]
    end_idx = p["end_idx"]
    event = p["event"]
    
    plt.style.use("dark_background")

    params = file["params"]

    bw = params["bandwidth"]

    iq_slice = np.fromfile(file_path, np.complex64, offset=start_idx*8, count=end_idx-start_idx)
    iq_slice = iq_slice - np.mean(iq_slice)

    plots = []

    plot_path = f"{cfg.site_path}/plots/waterfall_{event['datetime_str']}_station{file['station_id']}_FFT{cfg.NFFT}.png"
    plots.append(plot_path)

    if not os.path.exists(plot_path):

        print(f"Plotting event {event['datetime_readable']} NFFT={cfg.NFFT} ({file_path}[{start_idx}:{end_idx}]).")

        plt.figure(figsize=(7*len(iq_slice)/bw/(cfg.dt),6))
        Pxx, freqs, bins, im = plt.specgram(iq_slice, NFFT=cfg.NFFT, Fs=bw, noverlap=cfg.NFFT/2, cmap=cc.cm.bmw, xextent=(start_t, start_t+len(iq_slice)/bw))

        plt.ylabel("Doppler shift (Hz)")
        plt.xlabel("Time (sec)")
        plt.title(f"VMRE event (station {file['station_id']} {file['frequency']/1E6:.3f} MHz {event['datetime_readable']})")

        bottom, top = plt.ylim()
        plt.ylim((bottom+params["transition_width"], top-params["transition_width"]))

        cb = plt.colorbar()
        cb.remove()

        #vmin = 10 * np.log10(np.median(Pxx))
        #vmax = 10 * np.log10(np.max(Pxx))
        vmin = cfg.plot_min_dB
        vmax = cfg.plot_max_dB
        im.set_clim(vmin=vmin, vmax=vmax)

        plt.colorbar(im).set_label("Relative Power (dB)")
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()

    # audio = iq_slice.real
    # audio -= np.mean(audio)
    # factor = 32767 / (np.max(audio) - np.min(audio))
    # audio *= factor
    # scipy.io.wavfile.write(f"plots/{event['datetime_str']}_station{file['station_id']}.wav", params["bandwidth"], audio.astype(np.int16))

    return plots
