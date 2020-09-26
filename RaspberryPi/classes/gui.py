'''
@file gui.py
@brief Classes to manage the control parameters and user interface.
'''

from enum import Enum
import numpy

_class_debug = False

class PiSynthStatus(Enum):
    '''
    Defines the various status of the application.
    '''

    # Ready to accept commands, initialization complete
    # MIDI is working on current bank
    STANDBY = 1
    # The application is loading a new bank of samples
    LOADING = 2
    # The application is recording a sample
    RECORDING = 3
    # The application is set to record samples.
    # Any not button start recording a new sample, according
    # to the sampling parameters.
    SAMPLEMODE = 4

class Utilities():
    '''
    Cal utilities
    '''

    def calcFade1(fadeout_length):
        '''
        Calc the base fadeout

        :param fadeout_length: The base duration of the fadeout
        :return: The calculated fadeout
        '''

        return numpy.linspace(1., 0., fadeout_length)

    def calcFade2(fadeout):
        '''
        Power the base fadeout by a fixed number
        :return: The calculated fadeout
        '''

        return numpy.power(fadeout, 6)

    def calcFade3(fadeout, fadeout_length):
        '''
        Complete the fadeout calculation

        :return: The calculated fadeout
        '''

        return numpy.append(fadeout, numpy.zeros(fadeout_length, numpy.float32)).astype(numpy.float32)

    def calcStretchFactor():
        '''
        Calc the growing note speed to stretch the samples for the missing notes in the octave

        :return: The calculate speed
        '''

        return numpy.power(2, numpy.arange(0.0, 84.0) / 12).astype(numpy.float32)