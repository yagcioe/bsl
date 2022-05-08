import wavTools
import dereverb
import soundfile
import parameters as param

def run():
    wav = wavTools.loadWavFile('/workspace/training/KEC/2/speaker0.wav')
    tr ,comp = dereverb.compress(wav, 47, 10, 0, 5, 70, param.sampleRate)
    soundfile.write('/workspace/training/KEC/2/speaker0CompTr.wav',tr , param.sampleRate)
    soundfile.write('/workspace/training/KEC/2/speaker0CompCMP.wav',comp , param.sampleRate)
    
    derv = dereverb.deReverb(wav)
    soundfile.write('/workspace/training/KEC/2/speaker0Derev.wav',derv , param.sampleRate)