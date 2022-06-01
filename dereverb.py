from pedalboard import Pedalboard, Compressor, Mix, Gain, Invert
from . import environment as env


def buildPedalBoard(stacks) -> Pedalboard:
    def invertedCompression():
        return Pedalboard(plugins=[Invert(), Compressor(threshold_db=-53, ratio=10, attack_ms=0.05, release_ms=65)])

    def deverbStack():
        return Mix([invertedCompression(), Gain(gain_db=0)])

    return Pedalboard([deverbStack() for i in range(stacks)])


def deReverb(wav):
    board = buildPedalBoard(1)
    return board(wav, env.sampleRate)
