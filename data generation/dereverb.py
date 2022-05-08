import soundfile
import numpy as np

def deReverb(wav, sr):
    wi = phaseInvert(wav)
    trash, wi = compress(wi, 47, 10, 0, 5, 70, sr)
    print(wi)
    return [wav[i]+wi[i] for i in range(len(wav))]

def compress(data, threshold, ratio, makeup, attack, release, sr):
    """
    Reduces dynamic range of input signal by reducing volume above threshold.
    The gain reduction is smoothened according to the attack and release.
    Makeup gain must be added manually.
    Parameters
    ----------
    data: 
        array containing the signal in bits.
    threshold: scalar (dB)
        value in dB of the threshold at which the compressor engages in
        gain reduction.
    ratio: scalar
        The ratio at which volume is reduced for every dB above the threshold
        (i.e. r:1)
        For compression to occur, ratio should be above 1.0. Below 1.0, you
        are expanding the signal.

    makeup: scalar (dB)
        Amount of makeup gain to apply to the compressed signal

    attack: scalar (ms)
        Characteristic time required for compressor to apply full gain
        reduction. Longer times allow transients to pass through while short
        times reduce all of the signal. Distortion will occur if the attack
        time is too short.

    release: scalar (ms)
        Characteristic time that the compressor will hold the gain reduction
        before easing off. Both attack and release basically smoothen the gain
        reduction curves.

    wout: True/False, optional, default=True
        Writes the data to a 16 bit *.wav file. Equating to false will suppress
        *.wav output, for example if you want to chain process.

    plot: True/False, optional, default=True
        Produces plot of waveform and gain reduction curves.


    Returns
    -------
    data_Cs: array containing the compressed waveform in dB
    data_Cs_bit: array containing the compressed waveform in bits.
    """
    soundfile.read()
    data_dB = 20*np.log10(abs(data))
    n = len(data)
    # Array for the compressed data in dB
    dataC = data_dB.copy()
    # attack and release time constant
    a = np.exp(-np.log10(9)/(44100*attack*1.0E-3))
    re = np.exp(-np.log10(9)/(44100*release*1.0E-3))
    # apply compression

    for i in range(n):
        if dataC[i] > threshold:
            dataC[i] = threshold+(dataC[i]-threshold)/(ratio)
    # gain and smooth gain initialization
    gain = np.zeros(n)
    sgain = np.zeros(n)
    # calculate gain
    gain = np.subtract(dataC, data_dB)
    sgain = gain.copy()
    # smoothen gain

    for i in range(1, n):
        if sgain[i-1] >= sgain[i]:
            sgain[i] = a*sgain[i-1]+(1-a)*sgain[i]
        if sgain[i-1] < sgain[i]:
            sgain[i] = re*sgain[i-1]+(1-re)*sgain[i]
    # Array for the smooth compressed data with makeup gain applied
    dataCs = np.zeros(n)
    dataCs = data_dB+sgain+makeup
    # Convert our dB data back to bits
    dataCs_bit = 10.0**((dataCs)/20.0)
    # sign the bits appropriately:

    for i in range(n):
        if data[i] < 0.0:
            dataCs_bit[i] = -1.0*dataCs_bit[i]

    return dataCs, dataCs_bit


def phaseInvert(list):
    inverted = [-1*l for l in list]
    return inverted