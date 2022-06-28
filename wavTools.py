import random
import librosa
import numpy as np
import pyroomacoustics as pra
from pyroomacoustics.directivities \
    import (CardioidFamily, DirectionVector, DirectivityPattern)
from . import environment as env
import math
from .dereverb import deReverb
from . import performance as perf


def loadWavFile(path, offset=0, duration=None):
    wav, sr = librosa.load(path, sr=env.sampleRate, offset=offset,
                           duration=duration, mono=True)
    wav = librosa.util.normalize(wav)
    wav = deReverb(wav)

    return wav


def makeCardioid(direction):
    return CardioidFamily(
        orientation=DirectionVector(
            azimuth=direction[0], colatitude=direction[1], degrees=False),
        pattern_enum=DirectivityPattern.CARDIOID
    )


def createRoom(room_dim, rt60):
    e_absortion, max_order = pra.inverse_sabine(rt60, room_dim)
    room: pra.ShoeBox = pra.ShoeBox(room_dim, fs=env.sampleRate, materials=pra.Material(
        e_absortion), max_order=max_order)
    return room


def trackEndingSoon(tracks):
    if len(tracks) < 1:
        raise 'Tracks length must be greater than 0'

    min = tracks[0][-1].endTime
    pos = 0
    for i in range(len(tracks)):
        track = tracks[i]
        # empty tracks
        if(len(track) == 0):
            return i

        ts = track[-1]
        if(ts.endTime < min):
            min = ts.endTime
            pos = i
    return pos


def trackEndingLatest(tracks):
    if len(tracks) < 1:
        raise 'Tracks length must be greater than 0'

    max = tracks[0][-1].endTime
    pos = 0
    for i in range(len(tracks)):
        track = tracks[i]
        # empty tracks
        if(len(track) == 0):
            continue

        ts = track[-1]
        if(ts.endTime > max):
            max = ts.endTime
            pos = i
    return pos


def makeTimeOffsets(timeStamps):
    tracks = [[]for i in range(env.maxSpeakerAtOnce)]
    for ts in timeStamps:
        ts.setOffset(0)
    tracks[0].append(timeStamps[0])
    for s in timeStamps[1:]:

        posToFill = trackEndingSoon(tracks)
        posOfLastTrack = trackEndingLatest(tracks)

        minTimeOffset = 0 if len(
            tracks[posOfLastTrack]) == 0 else tracks[posOfLastTrack][-1].endTime
        minTimeOffset = max(minTimeOffset - env.max_speach_overlap, 0)
        maxTimeOffset = 0 if len(
            tracks[posOfLastTrack]) == 0 else tracks[posOfLastTrack][-1].endTime
        maxTimeOffset = maxTimeOffset + env.maxTimeDistanceBetweenSpeakers

        offset = np.random.rand()*(maxTimeOffset-minTimeOffset) + minTimeOffset
        s.setOffset(offset)
        tracks[posToFill].append(s)

    # random start time offset for all ts
    randStartTime = random.random()*env.max_rand_start_time
    for ts in timeStamps:
        ts.setOffset(ts.startTime + randStartTime)

    return tracks


def mixRoom(room: pra.ShoeBox, listenerEarPositions, listenerEarDirs, speakerPositions, speakerDirs, wavs, timeStamp):
    listenerEarDirs = list(map(lambda d: makeCardioid(d), listenerEarDirs))
    speakerDirs = list(map(lambda d: makeCardioid(
        [d[0]+math.pi, d[1]]), speakerDirs))  # turn speaker around

    mic_array = pra.MicrophoneArray(
        np.c_[listenerEarPositions[0], listenerEarPositions[1]], directivity=listenerEarDirs, fs=env.sampleRate)

    for i in range(len(speakerPositions)):
        room.add_source(
            position=speakerPositions[i],
            directivity=speakerDirs[i],
            signal=wavs[i],
            delay=timeStamp[i].startTime)
    room.add_microphone_array(mic_array)

    return room


def simulate(room: pra.ShoeBox):
    # perf.start()
    room.simulate()
    # perf.end()


def exportRoom(room: pra.ShoeBox, filepath):
    room.mic_array.to_wav(filepath, norm=True, bitdepth=np.float32)


def duration(wav):
    return librosa.samples_to_time(len(wav), sr=env.sampleRate)


def maxDuration():
    return librosa.frames_to_time(frames=env.maxWidthOfImage-1, sr=env.sampleRate, hop_length=env.hop_len, n_fft=env.n_fft)


def maxSample():
    return librosa.frames_to_samples(frames=env.maxWidthOfImage-1, hop_length=env.hop_len, n_fft=env.n_fft)


def timeToSample(time):
    return librosa.time_to_samples(times=time, sr=env.sampleRate)
