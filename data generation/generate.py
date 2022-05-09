import os
import shutil
import traceback
import numpy as np
import math
import soundfile
import json
from KecFileGenerator import VoiceLineGeneratorKEC
import environment as env
import wavTools
import util
import visualization as visual

env.overrideParams()


"""Room Functions"""


def generate_room_characteristics():
    dims = rt60 = absorption = 0
    if env.randomize_room:
        dims = [np.random.randint(env.room_dim_ranges[i][0], env.room_dim_ranges[i][1])
                for i in range(len(env.room_dim_ranges[:]))]

        rt60: float = env.rt60_range[0] + \
            (env.rt60_range[1]-env.rt60_range[0])*np.random.random()

        absorption: float = env.absorption_range[0] + \
            (env.absorption_range[1] -
             env.absorption_range[0]) * np.random.random()

    else:
        dims = env.normal_room_dim
        rt60 = env.normal_rt60
        absorption = env.normal_absorption

    return dims, rt60, absorption


def random_position_in_room(roomDims):
    x = np.random.random() * (roomDims[0]-1) + 0.5
    y = np.random.random() * (roomDims[1]-1) + 0.5
    z = 1.73
    return [x, y, z]


def positions_too_close(positions):
    for a in positions[1:]:
        for b in positions[1:]:
            if a == b:
                continue
            if util.distance(a, b) < 1:
                return True
    return False


def anlges_too_small(dirs):
    for i in range(len(dirs)):
        for j in range(i+1, len(dirs)):
            if(abs(dirs[i][0]-dirs[j][0]) < env.min_angle):
                return True
    return False


def transform_to_directivities(positions):
    dirs = []
    middle = [util.avg(np.transpose(positions)[i])
              for i in range(len(positions[0]))]

    listenerPos = positions[0]
    # Winkel aus Vogelperspeltive, in die Listnener guckt
    baseAngle = util.toAngle(listenerPos[:2], middle[:2])
    dirs.append([baseAngle, math.pi/2])

    for pos in positions[1:]:
        dirs.append([util.toAngle(listenerPos, pos), math.pi/2])

    return dirs, baseAngle, middle


def random_persons_in_room(roomDims, count):
    def pos_in_room(count):
        pos = []
        for i in range(count):
            pos.append(random_position_in_room(roomDims))
        return pos

    # do while: erzeuge solange bis gültiges ergebnis
    positions = pos_in_room(count)
    dirs, baseAngle, middle = transform_to_directivities(positions)
    while(positions_too_close(positions) or anlges_too_small(dirs)):
        positions = pos_in_room(count)
        dirs, baseAngle, middle = transform_to_directivities(positions)

    return positions, dirs, middle, baseAngle

# calculates mic positions depentend of middle point


def get_pos_mics(position, dir):
    dirLeft = [util.boundAngle(dir[0]+math.pi/2), dir[1]]
    dirRight = [util.boundAngle(dir[0] - math.pi/2), dir[1]]
    posLeft = point_pos(position, env.head_size/2, dirLeft[0])
    posRight = point_pos(position, env.head_size/2, dirRight[0])

    return [posLeft, posRight], [dirLeft, dirRight]

# calculates mic position depentend of middle point


def point_pos(x, d, theta):
    theta_rad = math.pi/2 - theta
    return [x[0] + d * math.cos(theta_rad), x[1] + d*math.sin(theta_rad), x[2]]


"""Exporting training data"""


def createJsonData(sampleNr: int, speakerIdsList, listenerPos, listenerDir,
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
    try:
        os.mkdir(targetFolder)
    except Exception as e:
        shutil.rmtree(targetFolder)
        os.mkdir(targetFolder)


def exportSample(sampleNr: int, roomWav, wavs, json_data: any, fig):
    folder = env.target_dir+'/'+str(sampleNr)
    createFolder(folder)
    # wavTools.exportRoom(room, folder+'/room.wav')
    soundfile.write(folder+'/room.wav', roomWav, env.sampleRate)
    for i in range(len(wavs)):
        soundfile.write(folder+f'/speaker{i}.wav', wavs[i], env.sampleRate)
    with open(folder+'/description.json', 'w', encoding='utf8') as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)
    if(env.exportFigures):
        fig.savefig(folder+"/figure.png", bbox_inches="tight")


"""MAIN"""


def generate():
    sampleNr = env.skipSamples
    gen = VoiceLineGeneratorKEC(
        env.target_amount_samples, env.speakers_in_room)
    for (wavs, timestamps) in gen:
        sampleNr += 1
        try:
            # creating parameters

            dims, rt60, absorption = generate_room_characteristics()
            room = wavTools.createRoom(dims, rt60, absorption)

            pos, dirs, middle, baseAnlge = random_persons_in_room(
                dims, env.speakers_in_room+1)
            listener_pos = pos[0]
            listener_dir = dirs[0]
            speakerPos = pos[1:]
            speakerDir = dirs[1:]

            earPos, earDirs = get_pos_mics(listener_pos, listener_dir)

            # creating data
            tracks = wavTools.makeTimeOffsets(timestamps)
            if env.visualize:
                visual.plotTracks(tracks)
            fig = visual.customPlot(pos, middle, dirs, baseAnlge, dims)

            room = wavTools.mixRoom(room, earPos, earDirs, speakerPos,
                                    speakerDir, wavs, timestamps)
            room.simulate()

            allListenerPos = [listener_pos]
            allListenerPos.extend(earPos)

            allListenerDirs = [listener_dir]
            allListenerDirs.extend(earDirs)

            # correct agnles offset
            allListenerPos = [util.rotateAroundPoint(v, listener_pos, -baseAnlge)
                              for v in allListenerPos]
            speakerPos = [util.rotateAroundPoint(v, listener_pos, -baseAnlge)
                          for v in speakerPos]
            allListenerPos = [util.translate(
                p, listener_pos) for p in allListenerPos]
            speakerPos = [util.translate(p, listener_pos) for p in speakerPos]
            allListenerDirs = [
                [util.boundAngle(d[0]-baseAnlge), d[1]] for d in allListenerDirs]
            speakerDir = [[util.boundAngle(d[0]-baseAnlge), d[1]]
                          for d in speakerDir]

            json_data = createJsonData(sampleNr, range(
                len(wavs)), allListenerPos, allListenerDirs, speakerPos, speakerDir, timestamps)
            roomWav = np.swapaxes(room.mic_array.signals, 0, 1)

            if env.verbose > 0:
                msg = f'Generated Room Nr.{sampleNr}.'
                print(msg)
            yield sampleNr, roomWav, wavs, json_data, fig
        except Exception as e:
            sampleNr -= 1
            if env.verbose > 0:
                print('error ' + str(e))
                traceback.print_exc()


if __name__ == '__main__':
    generator = generate()
    for (sampleNr, roomWav, wavs, json_data, fig) in generator:
        exportSample(sampleNr, roomWav, wavs, json_data, fig)
