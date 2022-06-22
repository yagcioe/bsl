import re
import numpy as np
import os
import textgrid
from .timestamp import SentenceWithTimestamp
from . import environment as env
from . import performance as perf
from .wavTools import loadWavFile


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


def rec_filter(x):
    return True if 'rec' in x else False


def matchingWavFile(txtName, allWavsNames):
    for wav in allWavsNames:
        if(txtName[:-8] in wav):
            return wav
    print('missing Wav file for: '+txtName)
    return None


def allWavGridTupels():
    # perf.start()
    src = '/workspace/data/KEC'
    recFolders = list(filter(lambda f: rec_filter(f), os.listdir(src)))
    allWavTxtTupels = []
    for rec in recFolders:
        currentDir = src+"/"+rec

        wavFilesOfFolder = list(
            filter(lambda f: wav_filter(f), os.listdir(currentDir)))

        txtFilesOfFolder = list(
            filter(lambda f: txt_filter(f), os.listdir(currentDir)))
        wavTxtTupel = []
        for t in txtFilesOfFolder:
            w = matchingWavFile(t, wavFilesOfFolder)
            if w != None:
                t = currentDir+"/"+t
                w = currentDir+"/"+w
                wavTxtTupel.append((t, w))

        allWavTxtTupels.extend(wavTxtTupel)
        wavFilesOfFolder = list(
            map(lambda f: currentDir+"/"+f, wavFilesOfFolder))
        txtFilesOfFolder = list(
            map(lambda f: currentDir+"/"+f, txtFilesOfFolder))
    # perf.end()
    return allWavTxtTupels


def split_sentence(textGrid: textgrid.textgrid.TextGrid):
    sentence = []
    sentences = []
    words = textGrid.getList('words')[0]
    specialWordsRegex = "<.*>"
    # sometimes the textgris has some false <P> placed in the middle of the sentence
    maxSentencePause = 1
    startTime = 0
    for word in words:
        if len(sentence) == 0:
            startTime = word.minTime

        #Satzende / pause erreicht
        if (re.search(specialWordsRegex, word.mark) != None and (word.maxTime-word.minTime) > maxSentencePause) \
                or word.maxTime-startTime > env.maxSpeakerDuration: # oder maximale satzdauer erreicht
            if len(sentence) >= env.min_words_per_sentence:
                sentences.append(SentenceWithTimestamp(
                    sentence, startTime, word.minTime))
            sentence = []
        # if it is real word and not just <P> or similar
        elif re.search(specialWordsRegex, word.mark) == None:
            sentence.append(word.mark)

    return sentences


def VoiceLineGeneratorKEC(count, voicesPerSample):
    tupelList = allWavGridTupels()
    for i in range(count):
        w,t = _createVoiceLineKEC(voicesPerSample,tupelList)
        yield w, t
    return


def _createVoiceLineKEC(voicesPerSample, tupelList):
    def getRec(path: str):
        split = path.split('/')
        return '/'.join(split[:-1])

    w = []
    t = []
    usedRec = []
    j = 0
    while j < voicesPerSample:
        j += 1
        ts, wav = (None, None)
        randomText = ''
        try:
            random_file = np.random.randint(0, len(tupelList))
            randomText, randomWav = tupelList[random_file]

            while env.prevent_SameRecordingInSampleTwice and getRec(randomText) in usedRec:
                if(env.verbose>1):
                    print(
                        f'tried to use same recoring twice: {randomText}: {usedRec}')
                random_file = np.random.randint(0, len(tupelList))
                randomText, randomWav = tupelList[random_file]
            sentences = split_sentence(
                textgrid.TextGrid.fromFile(randomText))

            random_phrase = np.random.randint(0, len(sentences))
            ts = sentences[random_phrase]
            wav = loadWavFile(
                randomWav, ts.startTime, ts.duration)
            usedRec.append(getRec(randomText))
        except Exception as e:
            if(env.verbose>0):
                print('could not load Data' + str(e))
            j -= 1
            continue

        t.append(ts)
        w.append(wav)
    return w,t
