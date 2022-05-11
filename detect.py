import datetime as dt
import os
from multiprocessing import Pool
import math
import json

import colorcet as cc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import config as cfg

c = 299792458.0

def detect(db):

    # For every dt second time period
    # for i in range(cfg.analyze_days * 24*60*60 // cfg.dt):
    t_analyze = []
    t_regions = []
    # for tstr in db["analyzed"]:
    for file in db["files"].values():

        if not file["analyze"]:
            continue

        t_start = dt.datetime.strptime(file["params"]["datetime_started"], cfg.time_format_data)
        t_end = t_start + dt.timedelta(seconds=(file["size"]//8)/file["params"]["bandwidth"])

        t_start = t_start.timestamp()
        t_end = t_end.timestamp()

        t_start = int(math.ceil(t_start/30)*30)
        t_end = int(math.floor(t_end/30)*30)

        for t in range(t_start, t_end, cfg.dt):
            already_analyzed = False
            for region in t_regions:
                if t >= region[0] and t+cfg.dt <= region[1]:
                    already_analyzed = True
                    break
            if not already_analyzed:
                t_analyze.append([t,db])
        
        t_regions.append((t_start, t_end))

        file["analyze"] = False

    with Pool(None) as p:
        new_events = p.map(detect_t, t_analyze)

    for event in new_events:
        if event is not None:
            db["events"][event["datetime_str"]] = event

def detect_t(x):

    np.seterr(divide='ignore') 

    t = x[0]
    db = x[1]
    t_P = []

    t_start = dt.datetime.fromtimestamp(t)
    t_end = dt.datetime.fromtimestamp(t+cfg.dt)

    t_start_str = dt.datetime.strftime(t_start, cfg.time_format)

    # Check which files have complete data for this period
    t_datafiles = []
    for datafile in db["files"].values():
        datafile_start = dt.datetime.strptime(datafile["start"], cfg.time_format)
        datafile_end = dt.datetime.strptime(datafile["end"], cfg.time_format)
        if t_start > datafile_start and t_end < datafile_end:
            t_datafiles.append(datafile)

    if not t_datafiles:
        return None

    # For each file
    for datafile in t_datafiles:
        
        datafile_start = dt.datetime.strptime(datafile["start"], cfg.time_format)
        datafile_idx = int((t_start - datafile_start).total_seconds() * datafile["bandwidth"])

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

        Pxx /= np.median(Pxx)

        if cfg.debug_plots:
            plt.imsave(f"plots/{t_start_str}-0-station{datafile['station_id']}-0-raw.png", Pxx)

        # Clip noise
        t_std = np.std(Pxx)
        t_thr = t_std*cfg.sig + 1
        Pxx = np.clip(Pxx - t_thr, 0, None)
        if cfg.debug_plots:
            plt.imsave(f"plots/{t_start_str}-0-station{datafile['station_id']}-1-clipped.png", Pxx)

        # Apply median filter
        Pxx = signal.medfilt2d(Pxx, 3)
        if cfg.debug_plots:
            plt.imsave(f"plots/{t_start_str}-0-station{datafile['station_id']}-2-median.png", Pxx)
        t_P.append(Pxx)

    t_P = np.asarray(t_P)
    nonzeros = np.count_nonzero(t_P, axis=0)
    if cfg.debug_plots:
        plt.imsave(f"plots/{t_start_str}-1-combined.png", nonzeros)

    E = np.sum(nonzeros)

    rows = np.sum(nonzeros, axis=1)
    freqshift = np.argmax(rows)* datafile['bandwidth']/len(rows) - datafile["bandwidth"]/2
    f = datafile["frequency"]
    velocity = c*freqshift/f

    energies = []
    observations = 0
    for i in range(cfg.min_observations-1, len(cfg.stations)):
        tmp = np.clip(nonzeros - i, 0, 1)
        if cfg.debug_plots:
            plt.imsave(f"plots/{t_start_str}-2-observations-{i+1}.png", tmp)
        e = np.sum(tmp)
        energies.append(e)
        if e >= cfg.thr[i]:
            observations = i+1

    # Threshold
    if observations > 0:
        print(f"t={t_start} {len(t_datafiles)=} {E=} {observations=} {energies=} {freqshift=} {velocity=}")
        return {
            "datetime_str": dt.datetime.strftime(t_start, cfg.time_format),
            "datetime_readable": dt.datetime.strftime(t_start, cfg.time_format_readable),
            "energy": float(E),
            "observations": observations,
            "freqshift": freqshift,
            "velocity": velocity,
        }
    else:
        return None
