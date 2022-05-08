
import math
"""Script parameters"""
target_amount_samples = 10
skipSamples = 0
target_dir = '/workspace/training/KEC'
visualize = True
verbose = False

prevent_SameRecordingInSampleTwice = False

"Persons"
# size of the Listeners head diameter
head_size = 0.2

speakers_in_room = 2
maxSpeakerAtOnce = 2
speaker_in_room_ranges = [1, 2]
randomize_speaker_count = False

#minimum_time_offset = 0.1 #sec
max_speach_overlap = 1 #sec
maxTimeDistanceBetweenSpeakers = 0.7  # sec

min_angle = math.pi/18 # min angle between speakers in relation to listener
"ROOM"


randomize_room = True
# room generation will be laplace distributed in these intervalls [width, length, height]
normal_room_dim = [15, 20, 4]
room_dim_ranges = [[3, 30], [3, 30], [2.5, 5]]

# The amout Walls absorb Sound
normal_absorption = 1.2
absorption_range = [1, 2]

# the time it take until the signal drops by 60 dB
normal_rt60 = 0.4
rt60_range = [0.25, 0.75]


"AUdio"
sampleRate = 16000
min_words_per_sentence = 6
padding = 1  # sec

# 'nice to have' for data generation
source_dataset = 'KEC - https://clarin.phonetik.uni-muenchen.de/BASRepository/index.php?target=Public/Corpora/KEC/KEC.1.php'
