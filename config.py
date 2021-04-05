stations = {
    1: {
        "grid": "CN89og",
        "operator": "Preston Thompson",
        "data_path": "data/station1",
        "radio": "RTLSDR",
        "antenna": "VHF turnstile",
        "location": "Coquitlam",
        "computer": "Ubuntu 20.04 x86-64"
    },
    2: {
        "grid": "",
        "operator": "Ken Arthurs",
        "data_path": "data/station2",
        "radio": "NESDR",
        "antenna": "VHF turnstile",
        "location": "Surrey",
        "computer": "Windows 10 x86-64",
    },
    3: {
        "grid": "",
        "operator": "Ken Arthurs",
        "data_path": "data/station3",
        "radio": "NESDR",
        "antenna": "VHF turnstile",
        "location": "Surrey",
        "computer": "Ubuntu 20.04 x86-64 Macbook Pro",
    },
}

# Analysis
power_threshold = 5
dt = 10
n = 1024

spec_end = 15
spec_start = -15

NFFTs = [512]
default_fft = 512

analyze_days = 20
