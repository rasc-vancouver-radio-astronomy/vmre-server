receivers = [
    {
        "data_path": "/mnt/str/pri/vmre/data/jansky/",
    }
]

# Analysis
power_threshold = 16
notch_bw = 20
dt = 1
n = 4096
#dt = 5
#n = 1024

spec_width = 30
spec_start = 5

NFFTs = [256, 512, 1024]
default_fft = 512

