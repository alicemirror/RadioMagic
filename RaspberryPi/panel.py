'''
@file panel.py
@brief Raspberry Pi control panel

Manages the GUI graphical buttons interface acting as control panel of the
Radio Magic musical synth components.

The control panel is the main program of the PiSynth module running on the
Raspberry Pi controlling the Audio acquisition, automatic sound sampling and
effects generators and more.

@note This version of the interface should work with 8 rows of 16 buttons per row
define in the GUI configuration file gui.json

@author Enrico Miglino <balearicdynamicw@gmail.com>
@version 1.0 build 15
@date September 2020
'''

import tkinter as tk
import numpy as np
from functools import partial
from time import sleep
from PIL import Image, ImageTk
import json

import numpy
import os
import sounddevice
import threading
import rtmidi_python as rtmidi
import samplerbox_audio

import pyaudio
import wave

from classes.music import Sound, PlayingSound, Ps
from classes.gui import PiSynthStatus

# ------------------------ Creation of the root GUI
window = tk.Tk()
window.state('normal')
window.title('PiSynth Control panel')
window.background = 'black'

# ------------------------ Screen resolution to parametrize the size of the buttons
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# ID of the audio device on the Raspberry Pi. Normal it is 0 (analog
# or 1 (digital). In this application we use an external USB audio card
# supporting also audio sampling, so the value will differ
audio_device_id = 0

# --------------------------------------------------------------
#                   Parameters & Constants
# --------------------------------------------------------------

# Buttons list
button = list()

# Debug flag. Set it to false to disable the debug messages
_debug = False

def debugMsg(m):
    '''
    Debug function
    :param m: The debug message
    '''
    if(_debug):
        print(m)

# Samples loading thread
LoadingThread = None
# Sample loading IRQ
LoadingInterrupt = False

# When a button on the control panel has been pressed. Bound to the
# corresponding mouse event on the corresponding widget button
isPressed = True
# When a button on the control panel has been released. Bound to the
# corresponding mouse event on the corresponding widget button
isReleased = False

# --------------------------------------------------------------
#                         Music Presets
# --------------------------------------------------------------

FADEOUTLENGTH = 30000
FADEOUT = numpy.linspace(1., 0., FADEOUTLENGTH)
FADEOUT = numpy.power(FADEOUT, 6)
FADEOUT = numpy.append(FADEOUT, numpy.zeros(FADEOUTLENGTH, numpy.float32)).astype(numpy.float32)
SPEED = numpy.power(2, numpy.arange(0.0, 84.0)/12).astype(numpy.float32)

samples = {}
playingnotes = {}
sustainplayingnotes = []
sustain = False
# Instance of the Ps class that makes the playingsounds array of pointers
# available from everywhere
ps = Ps

midi_in = [rtmidi.MidiIn(b'in')]
previous = []

# --------------------------------------------------------------
#                           GUI Functions
# --------------------------------------------------------------

def load_GUI_parameters():
    '''
    Load the GUI parameters from the gui.json file and create the
    buttons image list and the frame to include the buttons
    '''
    # Buttons grid size, rows
    global panel_rows
    # Buttons grid size, columns
    global panel_cols
    # Number of images (shaded colors) a button can have
    global max_button_images
    # The max number of function groups (associated to the same number of
    # button colors)
    global max_button_functions
    # The size of the square buttons
    global button_size
    # Full path of the samples (bank folders)
    global samples_path
    # Full path of the GUI images
    global images_path
    # Image files extension (jpeg or png)
    global image_extension
    # Buttons images list
    # Every button can assume one of the images in the list, according
    # to the applicaiton logic
    # The button images are named accordingly, in the format b<nn>.png
    global b_images
    # button image without associated functio
    global image_off_button
    # The frame that includes all the buttons.
    # The parameters for the border and pads will center the button grid
    # on the screen. Keep them fixed! Should be recalculated if the
    # button size or number of buttons change.
    global frame_container
    # Frame container border
    global f_border
    # Frame container pad x
    global f_padx
    # Frame container pad y
    global f_pady
    # Ma value for pholyphony output
    # This can be set higher, but 80 is a safe value
    global max_polyphony
    # The ID of the audio output device. In the case of the internal output it is
    # 0 or 1 depending on the setting of analog output or HDMI output. The USB
    # sound board has typically the id 2
    global audio_device_id
    # List with the names of the notes to load the samples
    # Every sample file name is the same of the note that should
    # associated in the selected bank. The missing notes are
    # calculated expanding and compressing the sample frequencies
    global note_names
    # Midi device name as it appears in the list of recognized
    # midi devices connected to the USB
    global midi_device
    # Recording sample rate (44 or 48 KHz
    global sampling_rate
    # Recording chunk size in bytes (will work fine with 4096)
    global recording_chunk_size
    # Recording channels. Currently only the mono recording is
    # supported by the audio card (1 channel)
    global input_channels
    # The current status of the system
    global synth_Status
    # The sample record duration (seconds)
    # The value should be included between 1 sec and 9 sec max.
    global sample_lenght

    # Loads the parameters main dictionary
    with open("gui.json") as file:
        dictionary = json.load(file)

    # Interface settings
    image_extension = dictionary['imageType']
    images_path = dictionary['images']
    max_button_images = int(dictionary['buttonImages'])
    max_button_functions = max_button_images
    samples_path = dictionary['samples']
    panel_rows = int(dictionary['rows'])
    panel_cols = int(dictionary['columns'])
    button_size = dictionary['buttonsize']
    f_border = int(dictionary['frame_border'])
    f_padx = int(dictionary['frame_padX'])
    f_pady = int(dictionary['frame_padY'])

    # Playing control parameters
    max_polyphony = int(dictionary['maxPolyphony'])
    audio_device_id = int(dictionary['audioDevice'])
    midi_device = dictionary['midiDevice']
    note_names = dictionary['note_names']

    # Recording settings
    sampling_rate = int(dictionary['recordSampleRate'])
    recording_chunk_size = int(dictionary['recordChunkSize'])
    input_channels = int(dictionary['recordChannels'])
    sample_lenght = int(dictionary['recordDuration'])

    # Check to the sample lenght limits
    if(sample_lenght < 1):
        sample_lenght = 1
    elif(sample_lenght > 9):
        sample_lenght = 9

    # Initial status when starting
    synth_Status = PiSynthStatus.STANDBY

    # The frame that includes all the buttons.
    # The parameters for the border and pads will center the button grid
    # on the screen. Keep them fixed! Should be recalculated if the
    # button size or number of buttons change.
    frame_container = create_frame_container()

    # Pack the frame container ready to include the buttons grid
    frame_container.pack(
        side=tk.TOP,
        fill=tk.BOTH
    )

    # Prepares the images for the graphic interface
    image_off_button = resize_image_button(images_path + dictionary['offButtonImage'] + image_extension)
    b_images = list(resize_image_button((images_path + "b%02d" + image_extension) % (i + 1))
                    for i in range(max_button_images))

def create_frame_container():
    '''
    Create the frame contained for the GUI buttons grid

    :return: the TkInter Frame object
    '''
    global f_border
    global f_padx
    global f_pady

    return tk.Frame(
        window,
        highlightcolor='black',
        highlightbackground='black',
        background="black",
        border=f_border,
        padx=f_padx,
        pady=f_pady
    )

def resize_image_button(name):
    '''
    Resize an image according to the button size

    The image is loaded from file in its original size, then it is
    resized and converted to an TkInter PhotoImage ovject for the
    buttons graphic surface

    :param name: The full path image file name
    :return: The PhotoImage object to be assigned to the button surface
    '''
    global button_size

    file = Image.open(name)
    newsize = (button_size, button_size)
    btn = file.resize(newsize)
    return ImageTk.PhotoImage(btn)

def get_button_id(row, col):
    '''
    Calculate the button id corresponding to the selected row and
    column in the panel grid

    Note that this mehod assumes that the buttons in the panel grid
    has been added to the buttons list following the row-by-row order
    and column-by-column

    :param row: the selected row
    :param col: the selected column
    :return: the button id in the list
    '''
    global panel_cols

    return (row * panel_cols) + col

def klik(event, n):
    '''
    Button click callback function

    If the _debug flag is set to true, every time the top left
    button is pressed all the other buttons are set to the same color

    :param event: The ID of the button event: 1 pressed, 0 released
    :param n: The ID of the clicked button
    '''
    global b_images
    global panel_cols
    global panel_rows
    global max_button_functions
    global current_bank
    global preset
    global synth_Status

    # n not zero
    debugMsg("click: " +str(n) + " event " + str(event))

    # List of the bank buttons to check if a bank change has been pressed
    bank_button_numbers = [15, 31, 47, 63, 79, 95, 111, 127]
    # List of the record buttons for every bank
    record_button_numbers = [14, 30, 46, 62, 78, 94, 110, 126]

    # Check if the button is a bank change buttons.
    # Only the pressed event button is accepted
    # If the bank is the same already loaded, do nothing
    if(event and (synth_Status == PiSynthStatus.STANDBY)):
        try:
            n_index = bank_button_numbers.index(n)
            # if the button is not the current bank
            if(n_index != current_bank):
                synth_Status = PiSynthStatus.LOADING
                load_bank_IDs(n_index)
                refresh_bank_buttons()
                preset = n_index
                LoadSamples()
        except:
            # No bank button found
            pass

    # Check if the button is the bank sample record.
    # This button enable or disable the record mode.
    # When the record mode is enabled, pressing any note button
    # from 1 to 12, left to right, for every row/octave
    # a new sample is read and saved on the corresopnding
    # note.

    if( (event is True) and (
            (synth_Status is PiSynthStatus.STANDBY) or
            (synth_Status is PiSynthStatus.RECORDING)
            ) ):
        try:
            n_index = record_button_numbers.index(n)

            # If the button is the current bank
            # change the status of the recording mode
            if(n_index == current_bank):
                # If recording mode is set, disable it
                if(synth_Status is PiSynthStatus.RECORDING):
                    synth_Status = PiSynthStatus.STANDBY
                    button[n].config(image=b_images[0])
                else:
                    # Set recording mode
                    synth_Status = PiSynthStatus.RECORDING
                    button[n].config(image=b_images[7])
                    # load_bank_IDs(n_index)
                    # refresh_bank_buttons()
                    # preset = n_index
                    # LoadSamples()
        except:
            # No recording button found
            pass

    # The note and octvae values are calculated here to reduce the
    # number of controls but until are not verified against the note status
    # (presence of a sample) it is not certain that correspond to a real value
    note = calc_note(n)
    octave = calc_octave(n)

    # Notes should be in the range of a full octave
    if( (note < 12)  and (synth_Status == PiSynthStatus.STANDBY) ):
        # Reduce the octave to a number between 0 and 7 (rows order)
        octave = (n // panel_rows) // 2
        # Check for the note in the corresponding octave
        if(octave == 0):
            if(octave1[note] == 1):
                play_sample(n, event)
        elif(octave == 1):
            if(octave2[note] == 1):
                play_sample(n, event)
        elif(octave == 2):
            if(octave3[note] == 1):
                play_sample(n, event)
        elif(octave == 3):
            if(octave4[note] == 1):
                play_sample(n, event)
        elif(octave == 4):
            if(octave5[note] == 1):
                play_sample(n, event)
        elif(octave == 5):
            if(octave6[note] == 1):
                play_sample(n, event)
        elif(octave == 6):
            if(octave7[note] == 1):
                play_sample(n, event)
        elif(octave == 7):
            if(octave8[note] == 1):
                play_sample(n, event)

def calc_note(n):
    '''
    Return the note number corresponding to the button (based on 16 buttons per row)

    The calculated value is base zero

    :param n: The button ID
    :return: The corresopnding note value
    '''
    global panel_rows
    global panel_cols

    button_col = n - (calc_octave(n) * panel_cols)

    return button_col

def calc_octave(n):
    '''
    Return the octave number corresponding to the button (based on 8 rows)

    The calculated value is base zero

    :param n: The button ID
    :return: The corresopnding octave value
    '''
    global panel_rows

    return (n // panel_rows) // 2

def make_panel():
    '''
    Create the initial buttons panel in off state, organized inside
    a frame of defined rows and columns and associate to every button
    a corresponding callback fucntion
    '''
    global b_images
    global panel_cols
    global panel_rows
    global frame_container
    global image_off_button
    global isPressed
    global isReleased

    # Fill the buttons list with the objects
    for i in range(panel_rows):
        for j in range(panel_cols):
            button.append(
                tk.Button(frame_container, image=image_off_button )
            )
            button[-1].grid(row=i, column=j)
            button[-1].activebackground='black'
            button[-1].height=button_size
            button[-1].width=button_size
            button[-1].border=8
            button[-1].background='black'
            button[-1].relief = 'sunken'
            # Bind the callback function to the button intercepting the two events pressed and released
            button[-1].bind("<ButtonPress-1>", lambda event, arg1=isPressed, arg2=get_button_id(i, j): klik(arg1, arg2) )
            button[-1].bind("<ButtonRelease-1>", lambda event, arg1=isReleased, arg2=get_button_id(i, j): klik(arg1, arg2) )

# --------------------------------------------------------------
#                       Bank Functions
# --------------------------------------------------------------

def load_bank_IDs(bank):
    '''
    Load the notes status array for one of the eight octaves of the
    selected bank
    :param bank: The desired bank number
    '''
    # The selected samples bank ID from 0 to 7. A max of 8 banks
    # are allowed
    global current_bank
    # Samples presence of the samples for every notes in the
    # corresponging octave #1.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave1
    # Samples presence of the samples for every notes in the
    # corresponging octave #2.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave2
    # Samples presence of the samples for every notes in the
    # corresponging octave #3.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave3
    # Samples presence of the samples for every notes in the
    # corresponging octave #4.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave4
    # Samples presence of the samples for every notes in the
    # corresponging octave #5.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave5
    # Samples presence of the samples for every notes in the
    # corresponging octave #6.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave6
    # Samples presence of the samples for every notes in the
    # corresponging octave #7.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave7
    # Samples presence of the samples for every notes in the
    # corresponging octave #8.
    # The name of the file in the corresponding note position is
    # the note name followed by the octave number from 1 to 7).
    global octave8
    # The calculated global volume to be assigned by default to
    # the currently selected bank.
    # The Json file should define the desired default volume,
    # calculated
    global globalvolume
    # The number of octaves to transpose the sample set (default 0)
    global globaltranspose
    # The velocity of the bank
    global globalvelocity

    # Build the Json selected bank file name
    j_name = "bank" + str(bank) + ".json"
    # Set the current bank ID
    current_bank = bank

    debugMsg("Loading " + j_name)

    with open(j_name) as file:
        dictionary = json.load(file)

    # Load the notes flags for every octave.
    # There are max eight octaves and the notes are
    # listed in the traditional order c, c#, d, d#, e, f, f#, a, a#, b
    # Every note that correspons a sample in the current bank has the
    # flag set to 1 else it is 0
    octave1 = dictionary['oct1']
    octave2 = dictionary['oct2']
    octave3 = dictionary['oct3']
    octave4 = dictionary['oct4']
    octave5 = dictionary['oct5']
    octave6 = dictionary['oct6']
    octave7 = dictionary['oct7']
    octave8 = dictionary['oct8']
    # Load the desired default volume for the bank samples and calculate
    # the corresponding volume for note playing
    calc_global_volume(float(dictionary['volume']))
    # Load the transposition of the octave for the whole bank
    # It should be a number between -7 and 7, where the value of 0
    # means no transposition.
    globaltranspose = int(dictionary['transpose'])
    globalvelocity = int(dictionary['velocity'])

    debugMsg(" Set globalvolume to " + str(globalvolume) +
             " transpose " + str(globaltranspose) +
             " velocity " + str(globalvelocity))

def refresh_bank_buttons():
    '''
    Refresh the buttons of the interface according to the current
    bank note flags
    '''
    global panel_rows
    global panel_cols
    global current_bank
    global image_off_button
    global octave1
    global octave2
    global octave3
    global octave4
    global octave5
    global octave6
    global octave7
    global octave8

    # Enable the buttons with a note in the bank (first 12 buttons from left)
    # Loop all the 12 notes and updates the 8 octaves
    for j in range(12):
        if(octave1[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(0, j)].config(image=b_images[5])
        else:
            button[get_button_id(0, j)].config(image= image_off_button)
        if(octave2[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(1, j)].config(image=b_images[5])
        else:
            button[get_button_id(1, j)].config(image= image_off_button)
        if(octave3[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(2, j)].config(image=b_images[5])
        else:
            button[get_button_id(2, j)].config(image= image_off_button)
        if(octave4[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(3, j)].config(image=b_images[5])
        else:
            button[get_button_id(3, j)].config(image= image_off_button)
        if(octave5[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(4, j)].config(image=b_images[5])
        else:
            button[get_button_id(4, j)].config(image= image_off_button)
        if(octave6[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(5, j)].config(image=b_images[5])
        else:
            button[get_button_id(5, j)].config(image= image_off_button)
        if(octave7[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(6, j)].config(image=b_images[5])
        else:
            button[get_button_id(6, j)].config(image= image_off_button)
        if(octave8[j] == 1):
            # Set the button of the color used for samples
            button[get_button_id(7, j)].config(image=b_images[5])
        else:
            button[get_button_id(7, j)].config(image= image_off_button)

    # Show the button corresponding to the selected bank (rightmost column)
    # and the sample button for the same bank (position 15)
    for i in range(panel_rows):
        if(current_bank == i):
            # Set the button with the corresponding bank select color
            button[get_button_id(i, 15)].config(image=b_images[1])
            button[get_button_id(i, 14)].config(image=b_images[0])
        else:
            button[get_button_id(i, 15)].config(image= image_off_button)
            button[get_button_id(i, 14)].config(image= image_off_button)

def play_sample(btn, status):
    '''
    Play the note corresponding to the note button parameter, according
    to the samples in the current loaded bank or stop playing it.

    :param btn: The ID of the note (corresponding to the button ID)
    :param status: if True, plays the sample else stop playing
    '''
    if(status):
        button[btn].config(image=b_images[3])
        MidiCallback([145, btn, 34], 0)
    else:
        button[btn].config(image=b_images[5])
        MidiCallback([145, btn, 0], 0)

def get_note_file_name(octave, note):
    '''
    Calculate the full path note file name based on the note id and the current
    selected bank

    :param octave: The selected octave of the bank
    :param note: The note id
    :return: The full path note sample file
    '''
    global note_names
    global current_bank

    note_file_name = note_names[note] + str(octave + 1) + ".wav"
    return samples_path + "B" + str(current_bank) + "/" + note_file_name

# --------------------------------------------------------------
#                    Audio and MIDI Callback
# --------------------------------------------------------------

def AudioCallback(outdata, frame_count, time_info, status):
    '''
    Callback associated to the audio hardware. It is executed when
    a MIDI message sends the playnote features.
    The audio callback is based on the samplerbox_audio library and
    can mix up to max_polyphony different audio buffers played together.

    :param outdata:
    :param frame_count:
    :param time_info:
    :param status:
    '''
    global globavolume

    rmlist = []
    ps.playingsounds = ps.playingsounds[-max_polyphony:]
    b = samplerbox_audio.mixaudiobuffers(ps.playingsounds, rmlist, frame_count, FADEOUT, FADEOUTLENGTH, SPEED)
    for e in rmlist:
        try:
            ps.playingsounds.remove(e)
        except:
            pass
    b *= globalvolume
    outdata[:] = b.reshape(outdata.shape)

def MidiCallback(message, time_stamp):
    '''
    Process the MIDI messages and plays the notes.

    :param message: The MIDI message packet
    :param time_stamp: The timestamp for correctly queue the messages
    '''
    global playingnotes, sustain, sustainplayingnotes
    global preset, globaltranspose, globalvolume
    global samples

    # Decode the MIDI message in its components
    messagetype = message[0] >> 4
    messagechannel = (message[0] & 15) + 1
    # Check if this MIDI message includes a note
    note = message[1] if len(message) > 1 else None
    midinote = note
    # Check if this MIDI message includes a specification of the velocity
    velocity = message[2] if len(message) > 2 else None

    debugMsg("MidiCallback message " + str(message) + " messagetype " + str(messagetype) +
             " messagechannel " + str(messagechannel) + " midinote " + str(midinote) +
             " velocity " + str(velocity))

    # Assumes the message type (9) note on with velocity 0 is
    # a message type (8) note off
    if messagetype == 9 and velocity == 0:
        messagetype = 8

    # If is a message type (9) note on apply eventual octave transposition and play
    # the note
    if messagetype == 9:
        debugMsg("messagetype is 9 (note on) globaltranspose " + str(globaltranspose))
        midinote += globaltranspose
        try:
            debugMsg("playing notes" + str(samples[midinote, velocity]))
            playingnotes.setdefault(midinote, []).append(samples[midinote, velocity].play(midinote))
        except:
            debugMsg("Exception, pass")
            pass

    # Process the message type (8) note off applyin the sustain if it is active
    elif messagetype == 8:  # Note off
        debugMsg("messagetype is 8 (note off) globaltranspose " + str(globaltranspose))
        midinote += globaltranspose
        if midinote in playingnotes:
            for n in playingnotes[midinote]:
                if sustain:
                    sustainplayingnotes.append(n)
                else:
                    n.fadeout(50)
            # Empty the played notes array
            playingnotes[midinote] = []

    # Process the message type (12) program change and load the
    # new group of samples.
    elif messagetype == 12:  # Program change
        debugMsg('Program change ' + str(note))
        preset = note
        LoadSamples()

    # Process the message type (11) for pedal off (associated to the sustain)
    # With note 64 and velocity < 64 (typical 0)
    elif (messagetype == 11) and (note == 64) and (velocity < 64):  # sustain pedal off
        for n in sustainplayingnotes:
            n.fadeout(50)
        sustainplayingnotes = []
        sustain = False

    # Process the message type (11) for pedal on (associated to the sustain)
    # With note 64 and velocity > 64 (typical 127)
    elif (messagetype == 11) and (note == 64) and (velocity >= 64):  # sustain pedal on
        sustain = True

def open_sound_device():
    '''
    Open the sound device according to the application configuration
    The function manages the exception.
    '''
    # The sound device instant.
    global sd
    try:
        sd = sounddevice.OutputStream(device=audio_device_id,
                                      blocksize=512,
                                      samplerate=44100,
                                      channels=2,
                                      dtype='int16',
                                      callback=AudioCallback)
        # Start the sound device
        sd.start()
        debugMsg('Opened audio device #%i' % audio_device_id)
    except:
        debugMsg('Invalid audio device #%i' % audio_device_id)
        exit(1)

# --------------------------------------------------------------
#                    Manage Playing Samples
# --------------------------------------------------------------

def calc_global_volume(vol):
    '''
    Calculate the global volume assigned to the loaded samples.

    :param vol: The desired volume in dB (a negative number)
    '''
    global globalvolume

    # Initialize the global volume to -12 dB (no sound)
    globalvolume = 10 ** (-12.0 / 20)  # -12dB default global volume
    # Apply the desired volume level
    globalvolume *= 10 ** (vol / 20)

def LoadSamples():
    global LoadingThread
    global LoadingInterrupt
    global samples

    if LoadingThread:
        LoadingInterrupt = True
        LoadingThread.join()
        LoadingThread = None

    LoadingInterrupt = False
    LoadingThread = threading.Thread(target=ActuallyLoad)
    LoadingThread.daemon = True
    LoadingThread.start()

def ActuallyLoad():
    '''
    Thread loading the bank wav samples in memory controlled by the
    function LoadSamples()
    '''
    global preset
    global globalvolume
    global globaltranspose
    global globalvelocity
    global samples_path
    global samples
    global playingnotes
    global sustainplayingnotes
    global sustain
    global octave1
    global octave2
    global octave3
    global octave4
    global octave5
    global octave6
    global octave7
    global octave8
    global synth_Status

    ps.playingsounds = []
    samples = {}

    # Button color in loading status
    button[(preset * 16) + 15].config(image=b_images[7])

    # Only 96 notes are used (12 notes x 8 octaves)
    # instead of 127.
    for midinote in range(0, 127):
        if LoadingInterrupt:
            return
        # Calculate the octave based on the note sequency
        octave = midinote // 12
        note = midinote % 12

        if( ((octave1[note] == 1) and (octave == 0) ) or
            ((octave2[note] == 1) and (octave == 1)) or
            ((octave3[note] == 1) and (octave == 2)) or
            ((octave4[note] == 1) and (octave == 3)) or
            ((octave5[note] == 1) and (octave == 4)) or
            ((octave6[note] == 1) and (octave == 5)) or
            ((octave7[note] == 1) and (octave == 6)) or
            ((octave8[note] == 1) and (octave == 7)) ):

            # Calculate the file name according to the note and octave
            # file = os.path.join(dirname, "%d.wav" % midinote)
            file = get_note_file_name(octave, note)
            debugMsg("midinote " + str(midinote) + " globalvelocity " +
                     str(globalvelocity) + " file " + file)
            samples[midinote, globalvelocity] = Sound(file, midinote, globalvelocity)

    initial_keys = set(samples.keys())
    for midinote in range(128):
        lastvelocity = None
        for velocity in range(128):
            if (midinote, velocity) not in initial_keys:
                samples[midinote, velocity] = lastvelocity
            else:
                if not lastvelocity:
                    for v in range(velocity):
                        samples[midinote, v] = samples[midinote, velocity]
                lastvelocity = samples[midinote, velocity]
        if not lastvelocity:
            for velocity in range(128):
                try:
                    samples[midinote, velocity] = samples[midinote-1, velocity]
                except:
                    pass
    if len(initial_keys) > 0:
        debugMsg('Preset loaded: ' + str(preset))
    else:
        debugMsg('Preset empty: ' + str(preset))

    # Button color in normal status
    button[(preset * 16) + 15].config(image=b_images[1])
    synth_Status = PiSynthStatus.STANDBY

# --------------------------------------------------------------
#                           Recording
# --------------------------------------------------------------

def record_sample(btn):
    global sampling_rate
    global recording_chunk_size
    global input_channels
    global synth_Status
    global sample_lenght
    global audio_device_id

    debugMsg("Recording sample")

    # Initial status when starting
    synth_Status = PiSynthStatus.RECORDING

    # Audio format 16-bit resolution
    form_1 = pyaudio.paInt16

    # Calculate the name of the file according to the note button
    note = calc_note(btn)
    octave = calc_octave(btn)
    wav_output_filename = get_note_file_name(octave, note)
    # Instance of the PyAudio library
    audio = pyaudio.PyAudio()

    # Create the pyaudio stream
    stream = audio.open(format=form_1, rate=sampling_rate, channels=input_channels,
                        input_device_index=audio_device_id, input=True,
                        frames_per_buffer=recording_chunk_size)

    frames = []

    # loop through stream and append audio chunks to frame array
    for ii in range(0, int((sampling_rate / recording_chunk_size) * sample_lenght)):
        data = stream.read(recording_chunk_size)
        frames.append(data)

    debugMsg("Recording finished")

    # stop the stream, close it, and terminate the pyaudio instantiation
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # save the audio frames as .wav file
    wavefile = wave.open(wav_output_filename, 'wb')
    wavefile.setnchannels(input_channels)
    wavefile.setsampwidth(audio.get_sample_size(form_1))
    wavefile.setframerate(sampling_rate)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()

    # Initial status when starting
    synth_Status = PiSynthStatus.RECORDING

    debugMsg("Sample saved")

# --------------------------------------------------------------
#                           Application
# --------------------------------------------------------------

if __name__ == "__main__":
    '''
    Main application
    '''
    # Initialize the GUI according to the json parameters
    load_GUI_parameters()
    # Load the first samples bank (max 8) by default
    load_bank_IDs(0)
    # Create the GUI
    make_panel()
    # Show the first default bank settings
    refresh_bank_buttons()

    open_sound_device()
    preset = 0
    LoadSamples()

    debugMsg('midi ports ' + str(midi_in[0].ports))
    midi_in.append(rtmidi.MidiIn(midi_device.encode()))
    midi_in[0].callback = MidiCallback
    # midi_in[0].open_port(b'Keystation Mini 32 20:0')
    midi_in[0].open_port(midi_device.encode())
    previous = midi_in[0].ports

    # Start the main loop application
    window.mainloop()