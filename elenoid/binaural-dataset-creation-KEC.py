import json
import math
import os
import random
import shutil
import librosa
import numpy as np
import pyroomacoustics as pra
import soundfile
import textgrid
from pyroomacoustics.directivities \
    import (CardioidFamily, DirectionVector, DirectivityPattern)

# total number of samples will be split even on available speaker parings, may not be to small (doesn't  work with 100)
target_amount_samples = 250

source_dataset = 'KEC - https://clarin.phonetik.uni-muenchen.de/BASRepository/index.php?target=Public/Corpora/KEC/KEC.1.php'

# source directory of KEC dataset
data_path = '/workspace/data/KEC/'

# path to target directory
target_path = '/workspace/pyroomaccoustics/aaron_workspace/target/'


"""
    simulation settigns
"""
# room generation will be laplace distributed in these intervalls [width, length, height]
# normal room size: room_dim = [15, 20, 4]
room_dim_ranges = [[3, 30], [3, 30], [2.5, 5]]

# The amout Walls absorb Sound
# normal absorption = 1.2
absorption_range = [1, 2]

# the time it take until the signal drops by 60 dB
# reverberant room rt60 = 0.5
rt60_range = [0.05, 0, 75]

sampleRate = 16000
#total_length = 30
max_audio_length = 30
#min_audio_length = 5
min_characters = 20


"""
    pyroomacoustics
"""

curr_path = ''
sample_nr = 0


"""
    filter functions
"""


def rec_filter(x):
    return True if 'rec' in x else False


def wav_filter(x):
    return True if '.wav' in x else False


def txt_filter(x):
    return True if '.TextGrid' in x else False


def as_filter(x):
    return True if 'AS' in x else False


def idx_filter_txt(x, y):
    return True if x[len(x) - 10] == y else False


def idx_filter_wav(x, y):
    return True if x[len(x) - 5] == y else False


def get_matching_txt(wav, txt):
    if 'AS' in wav:
        return filter(lambda x: idx_filter_txt(x, wav[len(wav)-5]), filter(lambda x: as_filter(x), txt))
    else:
        return filter(lambda x: idx_filter_txt(x, wav[len(wav)-5]), filter(lambda x: not as_filter(x), txt))


def get_id(wav):
    return wav[14:17]


def get_rec(wav):
    return wav[:7]


"""
    random position and resulting angles
"""


def generate_random_room_characteristics():
    dims: list(int) = [np.random.randint(room_dim_ranges[i, 0], room_dim_ranges[i, 1])
                       for i in range(len(room_dim_ranges[:]))]

    rt60: float = rt60_range[0] + \
        (rt60_range[1]-rt60_range[0])*np.random.random()

    absorption: float = absorption_range[0] + \
        (absorption_range[1]-absorption_range[0]) * np.random.random()

    return dims, rt60, absorption

# generates random positon inside the room, height is fixed on 1.73 at the moment


def random_pos(room_dim):
    pos = [random.random() * (room_dim[0] - 1), random.random()
           * (room_dim[1] - 1), 1.73]
    if pos[0] == 0:
        pos[0] += 1
    if pos[1] == 0:
        pos[1] += 1
    return pos


# returns random positions and derived directivities
def random_position(room_dim):
    positions = []

    while(True):
        for i in range(4):
            positions.append(random_pos(room_dim))
        if(position_check(positions)):
            break

    positions[1] = positions[0]
    dirs = get_directivities(positions)
    return positions, dirs

# returns distance between two points


def get_distance(a, b):
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

# checks if positons are not equal


def position_check(positions):
    for i in range(1, len(positions)):
        pos = positions[i]
        if i != 1 and get_distance(pos, positions[1]) < 1:
            return False
        if i != 2 and get_distance(pos, positions[2]) < 1:
            return False
        if i != 3 and get_distance(pos, positions[3]) < 1:
            return False
    return True


# turns clockwise angle into counter-clockwise
def angle_trunc(a):
    while a < 0.0:
        a += math.pi * 2
    return a

# returns angle between two points in degrees


def get_angle(a, b):
    deltaY = b[1] - a[1]
    deltaX = b[0] - a[0]
    return math.degrees(angle_trunc(math.atan2(deltaY, deltaX)))

# calculates directivities for all positions


def get_directivities(positions):
    dirs = []

    h = [(positions[2][0] + positions[3][0])/2,
         (positions[2][1] + positions[3][1])/2]

    posi = positions[0]
    angle = get_angle(posi[:2], h)

    dirs.append([(angle + 90) % 360, 90])  # bug somewhere here
    dirs.append([(angle + 270) % 360, 90])

    positions = positions[2:]

    for pos in positions:
        dirs.append([get_angle(pos, posi), 90])
    return dirs


"""
    audio creation
"""

# opens wave file for specified intervall, creates positions and dirs


def create_wav(speaker1, t1, speaker2, t2, curr_dir):

    offset = t1[0]
    duration = t1[1] - offset
    wav1, _ = librosa.load(speaker1, sr=sampleRate,
                           offset=offset, duration=duration, mono=True)
    #wav1 = librosa.util.normalize(wav1)

    offset = t2[0]
    duration2 = t2[1] - offset
    wav2, _ = librosa.load(speaker2, sr=sampleRate,
                           offset=offset, duration=duration2, mono=True)
    #wav2 = librosa.util.normalize(wav2)

    positions, dirs = random_position()

    mix_audio(wav1, wav2, positions, dirs, curr_dir)

    return positions, dirs

# calculates mic positions depentend of middle point


def get_pos_mics(position, dir):
    x = point_pos(position, 0.08, dir[0])
    y = point_pos(position, 0.08, dir[1])
    return [x, y]

# calculates mic position depentend of middle point


def point_pos(x, d, theta):
    theta_rad = math.pi/2 - math.radians(theta)
    return [x[0] + d * math.cos(theta_rad), x[1] + d*math.sin(theta_rad), 1.7]

# creates pyroomaccoustics directivity object


def make_dir_cardioid(dir):
    return CardioidFamily(
        orientation=DirectionVector(
            azimuth=dir[0], colatitude=dir[1], degrees=True),
        pattern_enum=DirectivityPattern.CARDIOID,
    )


# simulates audio in room and saves input and ouput
def mix_audio(audio1, audio2, positions, dirs, curr_path):

    directivites = []

    for dir in dirs:
        directivites.append(make_dir_cardioid(dir))

    mics_pos = get_pos_mics(positions[0], dirs[0])
    room_dim, rt60, absorption = generate_random_room_characteristics()
    e_absortion, max_order = pra.inverse_sabine(rt60, room_dim)
    room: pra.ShoeBox = pra.ShoeBox(room_dim, fs=sampleRate, materials=pra.Material(
        e_absortion), absorption=absorption, max_order=max_order)

    room.add_source(np.array(positions[1]),
                    signal=audio1, directivity=directivites[2])
    room.add_source(np.array(positions[2]),
                    signal=audio2, directivity=directivites[3])

    mic_array = pra.MicrophoneArray(
        np.c_[mics_pos[0], mics_pos[1]], directivity=directivites[:2], fs=sampleRate)

    room.add_microphone_array(mic_array)

    room.simulate()

    room.mic_array.to_wav(curr_path + '/' + str(sample_nr) +
                          '.wav', norm=True, bitdepth=np.float32)
    room.mic_array.to_wav(curr_path + '/speaker2.wav',
                          norm=True, bitdepth=np.float32)
    room.mic_array.to_wav(curr_path + '/speaker1.wav',
                          norm=True, bitdepth=np.float32)

    soundfile.write(curr_path + '/speaker1.wav',
                    data=audio1, samplerate=sampleRate)
    soundfile.write(curr_path + '/speaker2.wav',
                    data=audio2, samplerate=sampleRate)


"""
    text retrieval 
"""

#


def get_words_with_timestamps(timestamps_as, timestamps_is, j, word_as, word_is, word_ts_as, word_ts_is):
    max_as = timestamps_as[j][1]
    min_as = timestamps_as[j][0]

    max_is = timestamps_is[j][1]
    min_is = timestamps_is[j][0]

    words_as = get_words(word_as, word_ts_as, [min_as, max_as])
    words_is = get_words(word_is, word_ts_is, [min_is, max_is])

    return words_as, words_is


# retrives words with relative timestamp
def get_words(words, timestamps, interval):

    start = [(idx, time) for idx, time in enumerate(
        timestamps) if time[0] == interval[0]][0]
    end = [(idx, time) for idx, time in enumerate(
        timestamps) if time[1] == interval[1]][0]

    start_time = timestamps[start[0]][0]

    words = words[start[0]:end[0]+1]
    timestamps = timestamps[start[0]:end[0]+1]

    for idx, w in enumerate(words):
        words[idx] = [w, [timestamps[idx][0] -
                          start_time, timestamps[idx][1] - start_time]]
    return words

# splits text file in parts


def split_sentence(tg):

    helper = 0
    sentences, timestamp = [], []
    words, w_timestamp = [], []
    sentence = ''
    sentence_start = 0
    counter = 0

    for t in tg[0]:
        if helper > t.maxTime:
            break

        text = t.mark
        maxTime = t.maxTime
        minTime = t.minTime
        helper = maxTime
        sentence += ' ' + text
        words.append(text)
        w_timestamp.append([minTime, maxTime])
        counter += 1

        if '<P>' in text and maxTime - sentence_start < max_audio_length and maxTime - sentence_start >= 5 and len(sentence) > min_characters:
            sentences.append(sentence)
            sentence = ''
            timestamp.append([sentence_start, maxTime])
            sentence_start = maxTime

        elif '<P>' in text:
            sentence = ''
            sentence_start = maxTime
    return sentences, timestamp, words, w_timestamp


"""
    main functions
"""

# main function iterate through directories and call helper functions


def make_samples(rec, nr_samples_each):

    global sample_nr

    current_path = data_path + rec + '/'

    files = os.listdir(current_path)

    wav_as = list(filter(lambda x: as_filter(
        x), filter(lambda x: wav_filter(x), files)))
    wav_is = list(filter(lambda x: not as_filter(
        x), filter(lambda x: wav_filter(x), files)))
    txt = list(filter(lambda x: txt_filter(x), files))

    print('working on : ' + current_path)

    if len(wav_as) == 0:
        print('Error: no AS files found')
        return
    elif len(wav_is) == 0:
        print('Error: no IS files found')
        return

    nr_samples_each = int(nr_samples_each / len(wav_as))

    id_as = get_id(wav_as[0])
    id_is = get_id(wav_is[0])
    rec = get_rec(wav_as[0])

    root_dir = target_path + id_as + '-' + id_is
    dir_exists = False
    try:
        os.mkdir(root_dir)
    except:
        shutil.rmtree(root_dir)
        os.mkdir(root_dir)

    for i in range(len(wav_as)):
        w_as = wav_as.pop()
        w_is = wav_is.pop()

        txt_is = list(get_matching_txt(w_is, txt))
        txt_as = list(get_matching_txt(w_as, txt))

        try:
            tg_as = textgrid.TextGrid.fromFile(current_path + txt_as[0])
            tg_is = textgrid.TextGrid.fromFile(current_path + txt_is[0])

        except:
            print('Error: could not read ' + curr_path +
                  txt_as[0] + ' or ' + current_path + txt_is[0])
            print('Skipping iteration')
            continue

        sentences_as, timestamps_as, word_as, word_ts_as = split_sentence(
            tg_as)
        sentences_is, timestamps_is, word_is, word_ts_is = split_sentence(
            tg_is)

        print(nr_samples_each)

        for j in range(nr_samples_each):

            current_dir = root_dir + '/' + str(sample_nr)
            os.mkdir(current_dir)

            sentence_as = sentences_as[j]
            sentence_is = sentences_is[j]

            positions, dirs = create_wav(
                current_path + w_as, timestamps_as[j], current_path + w_is, timestamps_is[j], current_dir)
            words, words2 = get_words_with_timestamps(
                timestamps_as, timestamps_is, j, word_as, word_is, word_ts_as, word_ts_is)

            json_data = {
                'sample':
                [
                    {
                        'id': sample_nr, 'speaker 1': id_as, 'speaker 2': id_is,
                        'text speaker 1': sentence_as, 'text speaker 2': sentence_is,
                        'position 0': positions[0],
                        'directivity listener [azimuth, colatitude]': dirs[0],
                        'positions 1': positions[1],
                        'directvity listener [azimuth, colatitude]': dirs[1],
                        'positions 2': positions[2],
                        'directivity speaker 1 [azimuth, colatitude]': dirs[2],
                        'positions 3': positions[3],
                        'directivtiy speaker 2 [azimuth, colatitude]': dirs[3],
                        'source': source_dataset, 'words speaker1': words,
                        'words speaker2': words2
                    }
                ]
            }

            with open(current_dir + '/descriptor.json', 'w') as file:
                json.dump(json_data, file, indent=4)

            sample_nr += 1
            ratio = sample_nr/target_amount_samples
            # print(ratio)
            print(str(sample_nr/target_amount_samples*100) + '% created')


# start dataset creation
def start():

    print('dataset creation starts')
    recs = list(filter(lambda x: rec_filter(x), os.listdir(data_path)))
    size_recs = len(recs)
    nr_samples_each = int(target_amount_samples / size_recs)
    for rec in recs:
        make_samples(rec, nr_samples_each)
    print('done')


start()
