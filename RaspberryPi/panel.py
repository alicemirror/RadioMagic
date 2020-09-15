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
# @author Enrico Miglino <balearicdynamicw@gmail.com>
# @version 1.0 build 2
# @date September 2020

import tkinter as tk
import numpy as np
from functools import partial
from time import sleep
from PIL import Image, ImageTk
import json

# ------------------------ Creation of the root GUI
window = tk.Tk()
window.state('normal')
window.title('Py Synth Control panel')
window.background = 'black'

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

    # Loads the music lists
    with open("gui.json") as file:
        dictionary = json.load(file)

    image_extension = dictionary['imageType']
    images_path = dictionary['images']
    max_button_images = int(dictionary['buttonImages'])
    max_button_functions = max_button_images
    samples_path = dictionary['samples']
    panel_rows = dictionary['rows']
    panel_cols = dictionary['columns']
    button_size = dictionary['buttonsize']

    image_off_button = resize_image_button(images_path + dictionary['offButtonImage'] + image_extension)
    b_images = list(resize_image_button((images_path + "b%02d" + image_extension) % (i + 1))
                    for i in range(max_button_images))

def create_frame_container():
    '''
    Create the frame contained for the GUI buttons grid

    :return: the TkInter Frame object
    '''
    return tk.Frame(
        window,
        highlightcolor='black',
        highlightbackground='black',
        background="black",
        border=10,
        padx=24,
        pady=6
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
    global function_id

    # n not zero
    if (_debug):
        print("click: %d" % n)

    # When the top left button is pressed the colour is changed cyclically
    # Every color corresponds to a different set of features of the application
    if(n is 0):
        button[n].config(image=b_images[function_id])
        function_id += 1
        if(function_id is max_button_functions):
            function_id = 0

        # ---- Only for debug and testing
        if(_debug):
            print("click: %d" % n)
            for i in range(panel_rows):
                for j in range(panel_cols):
                    button[get_button_id(i, j)].config(image=b_images[function_id])
        #--- Debug end

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
#                   Parameters & Constants
# --------------------------------------------------------------

# # Buttons grid size, rows
# panel_rows = 0
# # Buttons grid size, columns
# panel_cols = 0
# # Number of images (shaded colors) a button can have
# max_button_images = 0
# # The max number of function groups (associated to the same number of
# # button colors)
# max_button_functions = 0
# # The size of the square buttons
# button_size = 0
# # Full path of the samples (bank folders)
# samples_path = ""
# # Full path of the GUI images
# images_path = ""
# # Image files extension (jpeg or png)
# image_extension = ""

# Number of different function groups, corresponding to different
# button colors.
# The button zero (top left corner) changes the functions group
function_id = 0

# Buttons list
button = list()

# Debug flag. Set it to false to disable the debug messages
_debug = True

# --------------------------------------------------------------
#                   Global calculations
# --------------------------------------------------------------

# # Buttons images list
# # Every button can assume one of the images in the list, according
# # to the applicaiton logic
# # The button images are named accordingly, in the format b<nn>.png
# b_images = list(resize_image_button("images/b%02d.png" % (i+1)) for i in range(max_button_images))
#
# image_off_button = resize_image_button("images/bNull.png")
#
# # The frame that includes all the buttons.
# # The parameters for the border and pads will center the button grid
# # on the screen. Keep them fixed! Should be recalculated if the
# # button size or number of buttons change.
# frame_container = create_frame_container()
#
# # Pack the frame container ready to include the buttons grid
# frame_container.pack(
#     side=tk.TOP,
#     fill=tk.BOTH
# )

# --------------------------------------------------------------
#                           Application
# --------------------------------------------------------------

if __name__ == "__main__":
    '''
    Main application
    '''
    load_GUI_parameters()
    make_panel()
    window.mainloop()