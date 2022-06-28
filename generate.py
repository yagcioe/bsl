import os
import random
import shutil
import traceback
from matplotlib import pyplot as plt
import numpy as np
import math
import soundfile
import json

from . import environment as env
from .KecFileGenerator import VoiceLineGeneratorKEC
from . import wavTools
from . import util
from . import visualization as visual
from . import performance as perf

env.overrideParams()


"""Room Functions"""


def generate_room_characteristics():
    # perf.start()
    dims = rt60 = 0
    if env.randomize_room:
        dims = [np.random.randint(env.room_dim_ranges[i][0], env.room_dim_ranges[i][1])
                for i in range(len(env.room_dim_ranges[:]))]

        rt60: float = env.rt60_range[0] + \
            (env.rt60_range[1]-env.rt60_range[0])*np.random.random()

    else:
        dims = env.normal_room_dim
        rt60 = env.normal_rt60

    # perf.end()
    return dims, rt60


def random_position_in_room(roomDims):
    x = np.random.random() * (roomDims[0]-1) + 0.5
    y = np.random.random() * (roomDims[1]-1) + 0.5
    z = 1.73
    return [x, y, z]


def positions_too_close(positions):
    for a in positions:
        for b in positions:
            if a == b:
                continue
            if util.distance(a, b) < 1:
                return True
    return False


def anlges_too_small(dirs):
    for i in range(len(dirs)):
        for j in range(i+1, len(dirs)):
            diff = abs(dirs[i][0]-dirs[j][0])
            if diff > math.pi:
                diff = math.pi*2-diff
            if(diff < env.min_angle):
                return True
    return False


def angles_too_big(dirs):
    for i in range(len(dirs)):
        for j in range(i+1, len(dirs)):
            diff = abs(dirs[i][0]-dirs[j][0])
            if diff > math.pi:
                diff = math.pi*2-diff
            if(diff > env.max_angle):
                return True
    return False


def transform_to_directivities(positions):
    listenerPos = positions[0]
    speakerPos = positions[1:]

    speakerDirs = [[util.toAngle(listenerPos, pos), math.pi/2]
                   for pos in speakerPos]

    miin = min(util.azimuth(speakerDirs))
    maax = max(util.azimuth(speakerDirs))
    diff = maax-miin
    if(diff > math.pi):
        t = maax
        maax = miin+2*math.pi
        miin = t
        diff = maax-miin

    # sanity checks
    dirToAdd = min(miin, maax)
    dirToReach = max(miin, maax)
    epsilon = 10**-6
    if(dirToAdd+diff - dirToReach > epsilon):
        raise 'idk what happend'

    upper = dirToAdd + math.pi/2  # ear angle
    lower = dirToReach-math.pi/2
    baseAngle = random.uniform(lower, upper)
    listenerDir = util.addColat(util.boundAngle(baseAngle))

    middle = util.toVektor(baseAngle, 2)
    middle = [-m for m in middle]
    middle = util.translate(listenerPos, middle)

    return listenerDir, speakerDirs, baseAngle, middle


def random_persons_in_room(roomDims, count):
    def pos_in_room(count):
        pos = []
        for i in range(count):
            pos.append(random_position_in_room(roomDims))
        return pos

    # do while: erzeuge solange bis gültiges ergebnis
    # perf.start()
    positions = pos_in_room(count)
    listenerDir, speakerDirs, baseAngle, middle = transform_to_directivities(
        positions)
    while(positions_too_close(positions) or anlges_too_small(speakerDirs) or angles_too_big(speakerDirs)):
        positions = pos_in_room(count)
        listenerDir, speakerDirs, baseAngle, middle = transform_to_directivities(
            positions)

    # perf.end()
    return positions, util.join([listenerDir], speakerDirs), middle, baseAngle

# calculates mic positions depentend of middle point


def get_pos_mics(position, dir):
    dirLeft = [util.boundAngle(dir[0]+math.pi/2), dir[1]]
    dirRight = [util.boundAngle(dir[0] - math.pi/2), dir[1]]
    posLeft = util.translateAngle(position, env.head_size/2, dirLeft[0])
    posRight = util.translateAngle(position, env.head_size/2, dirRight[0])

    return [posLeft, posRight], [dirLeft, dirRight]


"""Exporting training data"""


def createJsonData(sampleNr: int, duration, speakerIdsList, listenerPos, listenerDir,
                   speakrePositionList, speakerDirections, timestamps, words=None):
    speakers = []
    for i in range(len(speakerIdsList)):
        speaker = {
            'id': speakerIdsList[i],
            'position': speakrePositionList[i],
            'direction': {
                'azimuth': speakerDirections[i][0],
                'colatitude': speakerDirections[i][1],
            },
            'startTime': timestamps[i].startTime,
            'endTime': timestamps[i].endTime,
            'duration': timestamps[i].duration,
            'words': timestamps[i].sentence if hasattr(timestamps[i], 'sentence') else []
        }
        speakers.append(speaker)

    return {
        'sample': {
            'id': sampleNr,
            'duration': duration,
            'speakers': speakers,
            'listener': {
                'position': listenerPos[0],
                'direction': {
                    'azimuth': listenerDir[0][0],
                    'colatitude': listenerDir[0][1],
                },
                'positionLeft': listenerPos[1],
                'directionLeft': {
                    'azimuth': listenerDir[1][0],
                    'colatitude': listenerDir[1][1],
                },
                'positionRight': listenerPos[2],
                'directionRight': {
                    'azimuth': listenerDir[2][0],
                    'colatitude': listenerDir[2][1],
                },
            },
            'source': env.source_dataset
        }
    }


def createFolder(targetFolder):
    # perf.start()
    try:
        os.mkdir(targetFolder)
    except Exception as e:
        shutil.rmtree(targetFolder)
        os.mkdir(targetFolder)
    # perf.end()


def exportSample(sampleNr: int, roomWav, wavs, json_data: any, figs):
    # perf.start()
    folder = env.target_dir+'/'+str(sampleNr)
    createFolder(folder)
    soundfile.write(folder+'/room.wav',
                    np.swapaxes(roomWav, 0, 1), env.sampleRate)
    for i in range(len(wavs)):
        soundfile.write(folder+f'/speaker{i}.wav', wavs[i], env.sampleRate)
    with open(folder+'/description.json', 'w', encoding='utf8') as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)
    if(env.exportFigures):
        for i, fig in enumerate(figs):
            fig.savefig(folder+f'/figure{i}.jpg', bbox_inches="tight")
            plt.close(fig)
    perf.end()


"""MAIN"""


def generate(amount=env.target_amount_samples, sampleNr=env.skipSamples):
    gen = VoiceLineGeneratorKEC(amount, env.speakers_in_room)

    for (wavs, timestamps) in gen:
        sampleNr += 1
        try:
            # creating parameters
            # perf.start('generate')
            roomWav, json_data, figs = _calculateSample(
                wavs, timestamps, sampleNr)
            if(env.visualize):
                for fig in figs:
                    plt.figure(fig)
                    plt.show()

            if env.verbose > 1:
                msg = f'Generated Room {sampleNr} / {amount}.'
                print(msg, end="\r", flush=True)
                if sampleNr == amount:
                    print(msg)
            # perf.end('generate')

            yield sampleNr, roomWav, wavs, json_data, figs
        except Exception as e:
            sampleNr -= 1
            if env.verbose > 0:
                print('error ' + str(e))
                traceback.print_exc()

    if(env.showPerformanceSummary):
        perf.showSummary()


def _calculateSample(wavs, timestamps, sampleNr):

    tracks = wavTools.makeTimeOffsets(timestamps)

    # remove hopeless wavs
    for i, (w, t) in enumerate(zip(wavs, timestamps)):
        if t.startTime > wavTools.maxDuration():
            del wavs[i]
            del timestamps[i]

    # shorten tracks
    for i, (w, t) in enumerate(zip(wavs, timestamps)):
        paddingR = 2  # sec
        maxEnd = wavTools.maxDuration()-paddingR
        t.endTime = min(t.endTime, maxEnd)
        t.duration = t.endTime-t.startTime
        wavs[i] = w[:wavTools.timeToSample(t.duration)]  # shorten if nessesary

    # remove tracks that are too short
    for i, (w, t) in enumerate(zip(wavs, timestamps)):
        if t.duration < 1:
            del wavs[i]
            del timestamps[i]

    # creating parameters
    dims, rt60 = generate_room_characteristics()
    room = wavTools.createRoom(dims, rt60)

    pos, dirs, middle, baseAnlge = random_persons_in_room(
        dims, len(wavs)+1)
    listener_pos = pos[0]
    listener_dir = dirs[0]
    speakerPos = pos[1:]
    speakerDir = dirs[1:]

    earPos, earDirs = get_pos_mics(listener_pos, listener_dir)

    room = wavTools.mixRoom(room, earPos, earDirs, speakerPos,
                            speakerDir, wavs, timestamps)
    wavTools.simulate(room)

    normedearPos = util.normalizeAllPoints(
        earPos, listener_pos, baseAnlge)

    speakerPos = util.normalizeAllPoints(
        speakerPos, listener_pos, baseAnlge)
    speakerDir = util.normalizeAllAngles(speakerDir, baseAnlge)

    normedEarDirs = util.normalizeAllAngles(earDirs, baseAnlge)

    listener_pos = util.normalizePoint(
        listener_pos, listener_pos, baseAnlge)
    listener_dir = util.normalizeAngle(listener_dir, baseAnlge)

    allListenerPos = [listener_pos]
    allListenerPos.extend(normedearPos)

    allListenerDirs = [listener_dir]
    allListenerDirs.extend(normedEarDirs)

    roomWav = room.mic_array.signals

    l = len(roomWav[0])
    if l >= wavTools.maxSample():
        # shorten, if too long
        roomWav = roomWav[:, :wavTools.maxSample()]
    if(l < wavTools.maxSample()):
        # lengthen if too short
        diff = wavTools.maxSample()-l
        roomWav = np.append(roomWav, np.zeros((len(roomWav), diff)), axis=1)

    duration = wavTools.duration(roomWav[0])

    # creating data
    json_data = createJsonData(sampleNr, duration, range(
        len(wavs)), allListenerPos, allListenerDirs, speakerPos, speakerDir, timestamps)

    figs = []
    if env.visualize or env.exportFigures:
        figs.append(visual.plotTracks(tracks))

        fig1, fig2 = visual.customPlot(
            util.join(pos, earPos), middle, util.join(dirs, earDirs), baseAnlge, dims)
        figs.extend([fig2])

    return roomWav, json_data, figs


if __name__ == '__main__':
    generator = generate()
    for (sampleNr, roomWav, wavs, json_data, fig) in generator:
        exportSample(sampleNr, roomWav, wavs, json_data, fig)
