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

c = 299792458.0 # speed of light

def detect(db, files):

    # For every dt second time period
    t_analyze = []

    t_start = (dt.datetime.now() - dt.timedelta(days=cfg.days)).replace(hour=0,minute=0,second=0,microsecond=0)

    for i in range(cfg.days*24*60*60//cfg.dt):
        t = i * cfg.dt
        t_analyze.append((t_start+dt.timedelta(seconds=t),files))

    with Pool(None) as p:
        new_events = p.map(detect_t, t_analyze)
    
    # new_events = map(detect_t, t_analyze)

    for event in new_events:
        if event is not None:
            db["events"].append(event)

def detect_t(x):

    np.seterr(divide='ignore') 

    t_start = x[0]
    t_end = t_start + dt.timedelta(seconds=cfg.dt)
    files = x[1]
    t_P = []

    # Check which files have complete data for this period
    t_datafiles = []
    for datafile in files:
        if t_start > datafile["start"] and t_end < datafile["end"]:
            t_datafiles.append(datafile)

    if not t_datafiles:
        return None

    t_start_str = dt.datetime.strftime(t_start, cfg.time_format)

    # For each file
    for datafile in t_datafiles:
        
        datafile_idx = int((t_start - datafile["start"]).total_seconds() * datafile["bandwidth"])

        # Load the data
        iq_slice = np.fromfile(datafile["filename"], np.complex64, offset=datafile_idx*8, count=cfg.dt*datafile["bandwidth"])

        # Correct DC
        iq_slice = iq_slice - np.mean(iq_slice)

        # Calculate the spectrogram
        freqs, tims, Pxx = signal.spectrogram(
            iq_slice,
            nfft=cfg.n,
            fs=datafile["bandwidth"],
            noverlap=cfg.n/2,
            return_onesided=False
        )

        Pxx = np.abs(np.fft.fftshift(Pxx))

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

    energies = []
    observations = 0
    for i in range(0, len(cfg.stations)):
        tmp = np.clip(nonzeros - i, 0, 1)
        if cfg.debug_plots:
            plt.imsave(f"plots/{t_start_str}-2-observations-{i+1}.png", tmp)

        e = np.sum(tmp)
        energies.append(e)

        if e >= cfg.thr[i]:
            observations = i+1

            # Calculate Doppler
            rows = np.sum(tmp, axis=1)
            freqshift = np.argmax(rows) * datafile['bandwidth']/len(rows) - datafile['bandwidth']/2
            velocity = c*freqshift/datafile['frequency']

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
