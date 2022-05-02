Example data set can be found here; workspace/pyroomaccoustics/aaron_workspace/target

Possible to-do's:
 - normalize audios before audio simulaton, could use librosa.normalize
 - check behind back
 - combine different as and is
    - as und is generator, der random einen as oder is aus den ordnern rausholt. Dieser wird dann aus der liste entfehrnt, bis der generator resettet wird
        - load all; shuffle; yield until empty
 - make them not start at the same time 
     - let them have overlap and single speak time and silence
 - random room dimensions and characteristics