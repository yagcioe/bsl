import re
import numpy as np
import os
import textgrid
from timestamp import SentenceWithTimestamp
import parameters as param
from wavTools import loadWavFile


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



def FileGeneratorsKEC():
    src = '/workspace/data/KEC'
    recFolders = list(filter(lambda f: rec_filter(f), os.listdir(src)))
    allWavfiles = []
    alltxtFiles = []
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
        allWavfiles.extend(wavFilesOfFolder)
        txtFilesOfFolder = list(
            map(lambda f: currentDir+"/"+f, txtFilesOfFolder))
        alltxtFiles.extend(txtFilesOfFolder)

    return allWavfiles, alltxtFiles, allWavTxtTupels


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
        if('\\u' in word.mark):
            print('hierfehltderUmlat')
        # if found break wich is longer than 1 sec
        if re.search(specialWordsRegex, word.mark) != None and (word.maxTime-word.minTime) > maxSentencePause:
            if len(sentence) >= param.min_words_per_sentence:
                sentences.append(SentenceWithTimestamp(
                    sentence, startTime, word.minTime))
            sentence = []
        # if it is real word and not just <P> or similar
        elif re.search(specialWordsRegex, word.mark) == None:
            sentence.append(word.mark)

    return sentences


def VoiceLineGeneratorKEC(count, voicesPerSample):

    def getRec(path: str):
        split = path.split('/')
        return '/'.join(split[:-2])

    allWavPaths, allTxtPaths, tupelList = FileGeneratorsKEC()
    for i in range(count):
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

                while param.prevent_SameRecordingInSampleTwice and getRec(randomText) in usedRec:
                    print('tried to use same recoring twice')
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
                print('could not load Data' + str(e))
                j -= 1
                continue

            t.append(ts)
            w.append(wav)
        yield w, t
    return
