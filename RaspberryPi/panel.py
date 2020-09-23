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
@version 1.0 build 11
@date September 2020
'''

import tkinter as tk
import numpy as np
from functools import partial
from time import sleep
from PIL import Image, ImageTk
import json
# import tkSnack

# import wave
# import time
import numpy
import os
# import re
import sounddevice
import threading
# from chunk import Chunk
# import struct
import rtmidi_python as rtmidi
import samplerbox_audio

from classes.music import Sound, PlayingSound, Ps

# ------------------------ Creation of the root GUI
window = tk.Tk()
window.state('normal')
window.title('Py Synth Control panel')
window.background = 'black'
# tkSnack.initializeSnack(window)
# sound = tkSnack.Sound()

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
#Sample loading IRQ
LoadingInterrupt = False

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
# playingsounds = []
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
    global audio_device_id
    # List with the names of the notes to load the samples
    # Every sample file name is the same of the note that should
    # associated in the selected bank. The missing notes are
    # calculated expanding and compressing the sample frequencies
    global NOTES

    # Loads the parameters main dictionary
    with open("gui.json") as file:
        dictionary = json.load(file)

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
    max_polyphony = int(dictionary['maxPolyphony'])
    audio_device_id = int(dictionary['audioDevice'])
    NOTES = dictionary['note_names']

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

def klik(n):
    '''
    Button click callback function

    If the _debug flag is set to true, every time the top left
    button is pressed all the other buttons are set to the same color

    :param n: The ID of the clicked button
    '''
    global b_images
    global panel_cols
    global panel_rows
    global max_button_functions
    global current_bank

    # n not zero
    if (_debug):
        print("click: %d" % n)

    # Check if a bank change has been pressed. If the bank
    # is the same already loaded, do nothing
    if(n == 15):
        if (current_bank != 0):
            load_bank_IDs(0)
            refresh_bank_buttons()
    elif(n == 31):
        if (current_bank != 1):
            load_bank_IDs(1)
            refresh_bank_buttons()
    elif(n == 47):
        if (current_bank != 2):
            load_bank_IDs(2)
            refresh_bank_buttons()
    elif(n == 63):
        if (current_bank != 3):
            load_bank_IDs(3)
            refresh_bank_buttons()
    elif(n == 79):
        if (current_bank != 4):
            load_bank_IDs(4)
            refresh_bank_buttons()
    elif(n == 95):
        if (current_bank != 5):
            load_bank_IDs(5)
            refresh_bank_buttons()
    elif(n == 111):
        if (current_bank != 6):
            load_bank_IDs(6)
            refresh_bank_buttons()
    elif(n == 127):
        if (current_bank != 7):
            load_bank_IDs(7)
            refresh_bank_buttons()

    # The note and octvae values are caltulated here to reduce the
    # number of calc but until are not verified by the controls below,
    # it is not certain that correspond to a real value
    note = calc_note(n)
    octave = calc_octave(n)

    if(note < 12):
        octave = (n // panel_rows) // 2
        # Check for the note in the corresponding octave
        if(octave == 0):
            if(octave1[note] == 1):
                play_sample(n)
        elif(octave == 1):
            if(octave2[note] == 1):
                play_sample(n)
        elif(octave == 2):
            if(octave3[note] == 1):
                play_sample(n)
        elif(octave == 3):
            if(octave4[note] == 1):
                play_sample(n)
        elif(octave == 4):
            if(octave5[note] == 1):
                play_sample(n)
        elif(octave == 5):
            if(octave6[note] == 1):
                play_sample(n)
        elif(octave == 6):
            if(octave7[note] == 1):
                play_sample(n)
        elif(octave == 7):
            if(octave8[note] == 1):
                play_sample(n)

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

    # Fill the buttons list with the objects
    for i in range(panel_rows):
        for j in range(panel_cols):
            button.append(
                tk.Button(frame_container,
                    image=image_off_button,
                    command=partial(klik, get_button_id(i, j)))
            )
            button[-1].grid(row=i, column=j)
            button[-1].activebackground='black'
            button[-1].height=button_size
            button[-1].width=button_size
            button[-1].border=8
            button[-1].background='black'
            button[-1].relief = 'sunken'

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
    for i in range(panel_rows):
        if(current_bank == i):
            # Set the button with the corresponding bank select color
            button[get_button_id(i, 15)].config(image=b_images[1])
        else:
            button[get_button_id(i, 15)].config(image= image_off_button)

def play_sample(btn):
    '''
    Play the sample corresponding to the note button parameter, if a sample
    is present in the position of the current loaded bank.

    The unique button ID is decoded in row and column, corresponding to the
    octave and specific note.

    :param btn: The ID of the note (corresponding to the button ID
    '''
    global current_bank
    global panel_rows
    global panel_cols
    global max_button_images
    global max_button_functions
    global button_size
    global samples_path
    global images_path
    global _debug

    octave = calc_octave(btn)
    note = calc_note(btn)

    debugMsg(" Octave " + str(octave) +
              " note " + str(note) +
              " button " + str(btn) )

    sample_full_name = get_note_file_name(octave, note)

    debugMsg("playing " + sample_full_name)

    # # Read the file
    # sound.read(sample_full_name)
    # # Play sound
    # sound.play(blocking=1)

def get_note_file_name(octave, note):
    '''
    Calculate the full path note file name based on the note id and the current
    selected bank

    :param octave: The selected octave of the bank
    :param note: The note id
    :return: The full path note sample file
    '''
    global NOTES
    global current_bank

    note_file_name = NOTES[note] + str(octave + 1) + ".wav"
    return samples_path + "B" + str(current_bank) + "/" + note_file_name

# --------------------------------------------------------------
#                    Audio and MIDI Callback
# --------------------------------------------------------------

def AudioCallback(outdata, frame_count, time_info, status):
    '''

    :param outdata:
    :param frame_count:
    :param time_info:
    :param status:
    :return:
    '''
    # global playingsounds
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
    Process the MIDI messages

    :param message: The MIDI message packet
    :param time_stamp: The timestamp for correctly queue the messages
    :return:
    '''
    global playingnotes, sustain, sustainplayingnotes
    global preset, globaltranspose, globalvolume
    global samples

    # Decode the MIDI message in its components
    messagetype = message[0] >> 4
    messagechannel = (message[0] & 15) + 1
    note = message[1] if len(message) > 1 else None
    midinote = note
    velocity = message[2] if len(message) > 2 else None

    debugMsg("MidiCallback message " + str(message) + " messagetype " + str(messagetype) +
             " messagechannel " + str(messagechannel) + " midinote " + str(midinote) +
             " velocity " + str(velocity))

    # Assumes the message type (9) note on with velocity 0 as
    # message type (8) note off
    if messagetype == 9 and velocity == 0:
        messagetype = 8

    # If message type (9) note on apply eventual octave transposition and play
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
                # else:
                #     n.fadeout(50)
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
    global NOTES
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
    global NOTES
    global samples
    global playingnotes
    global sustainplayingnotes
    global sustain
    # global playingsounds
    global octave1
    global octave2
    global octave3
    global octave4
    global octave5
    global octave6
    global octave7
    global octave8

    ps.playingsounds = []
    samples = {}
    # globalvolume = 10 ** (-12.0/20)  # -12dB default global volume
    # globaltranspose = 0

    # use current folder (containing 0 Saw) if no user media containing samples has been found
    # samplesdir = samples_path if os.listdir(samples_path) else '.'

    # basename = next((f for f in os.listdir(samplesdir) if f.startswith("%d " % preset)), None)      # or next(glob.iglob("blah*"), None)
    # if basename:
    #     dirname = os.path.join(samplesdir, basename)
    # if not basename:
    #     debugMsg('Preset empty: %s' % preset)
    #     return
    # debugMsg('Preset loading: %s (%s)' % (preset, basename))

    # definitionfname = os.path.join(dirname, "definition.txt")

    # if os.path.isfile(definitionfname):
    #     with open(definitionfname, 'r') as definitionfile:
    #         for i, pattern in enumerate(definitionfile):
    #             try:
    #                 # globalvolume already set when reading from the json bank file
    #                 # if r'%%volume' in pattern:        # %%paramaters are global parameters
    #                 #     globalvolume *= 10 ** (float(pattern.split('=')[1].strip()) / 20)
    #                 #     continue
    #
    #                 # globaltranspose already set when reading from the json bank file
    #                 # if r'%%transpose' in pattern:
    #                 #     globaltranspose = int(pattern.split('=')[1].strip())
    #                 #     continue
    #                 defaultparams = {'midinote': '0', 'velocity': '127', 'notename': ''}
    #
    #                 if len(pattern.split(',')) > 1:
    #                     defaultparams.update(dict([item.split('=') for item in pattern.split(',', 1)[1].replace(' ', '').replace('%', '').split(',')]))
    #                 pattern = pattern.split(',')[0]
    #                 pattern = re.escape(pattern.strip())
    #                 pattern = pattern.replace(r"\%midinote", r"(?P<midinote>\d+)").replace(r"\%velocity", r"(?P<velocity>\d+)")\
    #                                  .replace(r"\%notename", r"(?P<notename>[A-Ga-g]#?[0-9])").replace(r"\*", r".*?").strip()    # .*? => non greedy
    #                 for fname in os.listdir(dirname):
    #                     if LoadingInterrupt:
    #                         return
    #                     m = re.match(pattern, fname)
    #                     if m:
    #                         info = m.groupdict()
    #                         midinote = int(info.get('midinote', defaultparams['midinote']))
    #                         velocity = int(info.get('velocity', defaultparams['velocity']))
    #                         notename = info.get('notename', defaultparams['notename'])
    #                         if notename:
    #                             midinote = NOTES.index(notename[:-1].lower()) + (int(notename[-1])+2) * 12
    #                         samples[midinote, velocity] = Sound(os.path.join(dirname, fname), midinote, velocity)
    #             except:
    #                 debugMsg('Error in definition file, skipping line %s.' % (i+1))

    # else:

    # Only 96 notes are used (12 notes x 8 octaves)
    # instead of 127
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
    # for port in midi_in[0].ports:
    #     if port not in previous and 'Midi Through' not in port:
    midi_in.append(rtmidi.MidiIn(b'Keystation Mini 32 20:0'))
    midi_in[0].callback = MidiCallback
    midi_in[0].open_port(b'Keystation Mini 32 20:0')
            # print('Opened MIDI: ' + port)
    previous = midi_in[0].ports

    # Start the main loop application
    window.mainloop()