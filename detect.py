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

    # For every dt second time period
    # for i in range(cfg.analyze_days * 24*60*60 // cfg.dt):
    for tstr in db["analyzed"]:

        if db["analyzed"][tstr]:
            continue

        # t = t0 + dt.timedelta(seconds=i*cfg.dt)
        t = dt.datetime.strptime(tstr, cfg.time_format)
        t_end = t + dt.timedelta(seconds=cfg.dt)

        # Check which files have complete data for this period
        t_datafiles = []
        for datafile in db["files"].values():
            datafile_start = dt.datetime.strptime(datafile["start"], cfg.time_format)
            datafile_end = dt.datetime.strptime(datafile["end"], cfg.time_format)
            if t > datafile_start and t_end < datafile_end:
                t_datafiles.append(datafile)

        t_P = []
        # For each file
        for datafile in t_datafiles:
            
            datafile_start = dt.datetime.strptime(datafile["start"], cfg.time_format)
            datafile_idx = int((t - datafile_start).total_seconds() * datafile["bandwidth"])

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

            t_std = np.std(Pxx)
            #t_thr = 10**(cfg.clip_dB/10)
            t_thr = t_std*cfg.sig + np.median(Pxx)
            Pxx = np.clip(Pxx - t_thr, 0, None)
            t_P.append(Pxx)

        t_P = np.asarray(t_P)
        nonzeros = np.count_nonzero(t_P, axis=0)
        nonzeros = np.clip(nonzeros - 1, 0, 1)
        P = np.multiply(np.sum(t_P, axis=0), nonzeros)
        E = 10*np.log10(np.sum(P))

        print(f"t={t} {len(t_datafiles)=} {E=}")

        # Threshold
        if E > cfg.thr:
            db["events"].append({
                "datetime_str": dt.datetime.strftime(t, cfg.time_format),
                "datetime_readable": dt.datetime.strftime(t, cfg.time_format_readable),
                "energy": E,
            })
            print("Event!")
        
        db["analyzed"][tstr] = True
