receivers = [
    # {
    #     "ip": "jansky.carpetandbricks.com",
    #     "ssh_port": 3778,
    #     "data_path": "meteors/data_test",
    # }
    {
        "ip": "neptune",
        "ssh_port": 22,
        "data_path": "meteor_test_data/",
    }
]

# Analysis
power_threshold = 20
notch_bw = 20
#dt = 1
#n = 4096
dt = 5
n = 1024

spec_width = 30
spec_start = 5

NFFTs = (128, 256, 512, 1024)
default_fft = 512
