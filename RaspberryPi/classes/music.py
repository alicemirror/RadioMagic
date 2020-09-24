'''
@file music.py
@brief Classes to manage the audio playing and MIDI
'''

import wave
import time
import os
import re
import numpy
import sounddevice
import threading
from chunk import Chunk
import struct
import rtmidi_python as rtmidi
# Cython compiled audio engine .so file
import samplerbox_audio

_class_debug = False

class Ps():
    def __init__(self):
        self.playingsounds = []

class waveread(wave.Wave_read):
    '''
    Manages the file acquisition, check the wav coherence and
    get the loop markers, ifany.
    '''
    def initfp(self, file):
        '''
        Initialize the file pointer.
        This method check the selected file for validity based on its header content
        and read the various chunk types

        :param file:  The file to inizialize
        '''
        self._convert = None
        self._soundpos = 0
        self._cue = []
        self._loops = []
        self._ieee = False
        self._file = Chunk(file, bigendian=0)

        # Check for RIFF id in the file header
        if self._file.getname() != b'RIFF':
            raise Exception('file does not start with RIFF id')
        ## Check that file is a wav
        if self._file.read(4) != b'WAVE':
            raise Exception('not a WAVE file')

        # Number of chuncks read from file
        self._fmt_chunk_read = 0
        # Content of the current data chunk
        self._data_chunk = None

        # Read the wav file in chunks until the end of file
        # and organizes properly the chunks
        while 1:
            self._data_seek_needed = 1
            try:
                chunk = Chunk(self._file, bigendian=0)
            except EOFError:
                # Stop on end of file
                break
            chunkname = chunk.getname()
            if chunkname == b'fmt ':
                # Chunk is the file format
                self._read_fmt_chunk(chunk)
                self._fmt_chunk_read = 1
            elif chunkname == b'data':
                # Chunk is a data block
                if not self._fmt_chunk_read:
                    raise Exception('data chunk before fmt chunk')
                #update the data and calculate the number of frames (integer division)
                self._data_chunk = chunk
                self._nframes = chunk.chunksize // self._framesize
                self._data_seek_needed = 0
            elif chunkname == b'cue ':
                # Chunck is a marker
                numcue = struct.unpack('<i', chunk.read(4))[0]
                for i in range(numcue):
                    id, position, datachunkid, chunkstart, blockstart, sampleoffset = struct.unpack('<iiiiii', chunk.read(24))
                    self._cue.append(sampleoffset)
            elif chunkname == b'smpl':
                # Chunck name is sample, extract the loops parts.
                manuf, prod, sampleperiod, midiunitynote, midipitchfraction, smptefmt, smpteoffs, numsampleloops, samplerdata = struct.unpack(
                    '<iiiiiiiii', chunk.read(36))
                for i in range(numsampleloops):
                    cuepointid, type, start, end, fraction, playcount = struct.unpack('<iiiiii', chunk.read(24))
                    self._loops.append([start, end])
            # Skip the chunk is none of the previous conditions are satisafied
            chunk.skip()
        if not self._fmt_chunk_read or not self._data_chunk:
            raise Exception('fmt chunk and/or data chunk missing')

    def getmarkers(self):
        '''
        Get the marker, if any, from the chunk currently reading

        :return: The current marker
        '''
        return self._cue

    def getloops(self):
        '''
        Get the loops from the chunk currently reading

        :return: The number of loops in the sample
        '''
        return self._loops

class PlayingSound:
    '''
    Note sound player for MIDI
    '''
    def __init__(self, sound, note):
        '''

        :param sound:
        :param note:
        '''
        self.sound = sound
        self.pos = 0
        self.fadeoutpos = 0
        self.isfadeout = False
        self.note = note
        self.playingsounds = Ps.playingsounds

    def fadeout(self, i):
        '''
        Force the fadeout to true, regardless of the parameter

        :param i:
        :return:
        '''

        self.isfadeout = True

    def stop(self):
        '''
        Try to stop the current playing sound list

        '''
        try:
            playingsounds.remove(self)
        except:
            pass

class Sound:
    '''
    Manages the MIDI sound wave samples
    '''
    def __init__(self, filename, midinote, velocity):
        '''

        :param filename:
        :param midinote:
        :param velocity:
        '''

        if(_class_debug): print("D: filename " + filename)

        wf = waveread(filename)
        self.fname = filename
        self.midinote = midinote
        self.velocity = velocity
        if wf.getloops():
            self.loop = wf.getloops()[0][0]
            self.nframes = wf.getloops()[0][1] + 2
        else:
            self.loop = -1
            self.nframes = wf.getnframes()

        self.data = self.frames2array(wf.readframes(self.nframes), wf.getsampwidth(), wf.getnchannels())

        wf.close()

    def play(self, note):
        '''
        Append the selected note playing as an instance
        of the Sound class

        :param note: The selected note
        :return:  the PlayinSound class instance with the new appaended playing note
        '''

        snd = PlayingSound(self, note)
        snd.playingsounds.append(snd)
        return snd

    def frames2array(self, data, sampwidth, numchan):
        '''

        :param data:
        :param sampwidth:
        :param numchan:
        :return:
        '''
        if sampwidth == 2:
            npdata = numpy.fromstring(data, dtype=numpy.int16)
        elif sampwidth == 3:
            npdata = samplerbox_audio.binary24_to_int16(data, len(data)/3)
        if numchan == 1:
            npdata = numpy.repeat(npdata, 2)
        return npdata
