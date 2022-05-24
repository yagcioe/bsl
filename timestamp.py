class Timestamp:

    def __init__(self, start: float, end: float):
        self.startTime = start
        self.endTime = end
        self.duration = self.endTime-self.startTime

    def toTimestap(self):
        return [self.startTime, self.endTime, self.duration]

    def setOffset(self, offset: float):
        self.startTime = offset
        self.endTime = self.duration + offset

    def __str__(self):
        return f'Start: {self.startTime}, End:{self.endTime}, Duration:{self.duration}'

    def __repr__(self):
        return self.__str__()


class SentenceWithTimestamp(Timestamp):
    def __init__(self, sentence, start: float, end: float):
        self.sentence = sentence
        Timestamp.__init__(self,start, end)

    def __str__(self):
        return f'Sentence: {str(self.sentence)}, ' + Timestamp.__str__(self)

    def __repr__(self):
        return self.__str__()