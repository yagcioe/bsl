import math
import time
import wavTools
import dereverb
import soundfile
import util
import environment as env

env.overrideParams()

def run():
    wav = wavTools.loadWavFile('/workspace/training/KEC/2/speaker0.wav')
    print(wav)
    print(wav.shape)
    derv = dereverb.deReverb(wav)
    print(derv)
    print(derv.shape)
    soundfile.write('/workspace/training/KEC/2/speaker0Derev.wav',derv , env.sampleRate)

def speedTest():
    n=1000
    start = time.time_ns()
    for i in range(n):
        if(i%100==0):print(str(i)+"/"+str(n))
        wav = wavTools.loadWavFile('/workspace/training/KEC/2/speaker0.wav')
    
    for i in range(n):
        if(i%100==0):print(str(i)+"/"+str(n))
        wav = wavTools.loadWavFile('/workspace/training/KEC/2/speaker0.wav')

def typeCheck():
    simple= [0.1,math.pi/2]
    nested= [[0.1,math.pi/2],[0.2,math.pi/2]]

    print(util.azimuth(simple))
    print(util.azimuth(nested))