# @file panel.py
# @brief Raspberry Pi control panel
#
# Manages the GUI graphical buttons interface acting as control pane of the
# Radio Magic musical synth components.
#
# The control panel is the main program of the PiSynth module running on the
# Raspberry Pi controlling the Audio acquisition, automatic sound sampling and
# effects generators and more.
#
# Note that this version of the interface should work with 8 rows of 16 buttons per row
# define in the GUI configuration file gui.json
#
# @author Enrico Miglino <balearicdynamicw@gmail.com>
# @version 1.0 build 7
# @date September 2020

import tkinter as tk
import numpy as np
from functools import partial
from time import sleep
from PIL import Image, ImageTk
import json
#from playsound import playsound
import tkSnack

# ------------------------ Creation of the root GUI
window = tk.Tk()
window.state('normal')
window.title('Py Synth Control panel')
window.background = 'black'
tkSnack.initializeSnack(window)
sound = tkSnack.Sound()

# ------------------------ Screen resolution to parametrize the size of the buttons
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

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
    Load the notes status array for the eight octaves of the
    selected bank
    :param bank: The bank number
    '''
    # The selected samples bank
    global current_bank
    global octave1
    global octave2
    global octave3
    global octave4
    global octave5
    global octave6
    global octave7
    global octave8

    # Loads the music bank note IDa
    j_name = "bank" + str(bank) + ".json"
    # Set the current bank
    current_bank = bank

    if(_debug):
        print("loading " + j_name)

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

def refresh_bank_buttons():
    '''
    Refresh the buttons of the interface according to the current
    bank note flags
    '''
    global panel_rows
    global panel_cols
    global current_bank
    global image_off_button

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

    if(_debug):
        print(" Octave " + str(octave) +
              " note " + str(note) +
              " button " + str(btn) )

    # Note prefix file names
    note_names = ("c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b")
    # Create the file name of the note and octave based on the samples file name format
    note_file_name = note_names[note] + str(octave + 1) + ".wav"
    # Create the full path note name according to the current samples bank
    sample_full_name = samples_path + "B" + str(current_bank) + "/" + note_file_name

    if(_debug):
        print("playing " + sample_full_name)

    # Read the file
    sound.read(sample_full_name)
    # Play sound
    sound.play(blocking=1)

# --------------------------------------------------------------
#                   Parameters & Constants
# --------------------------------------------------------------

# Buttons list
button = list()

# Debug flag. Set it to false to disable the debug messages
_debug = True

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
    # Start the main loop application
    window.mainloop()