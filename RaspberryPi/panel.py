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
# @version 1.0 build 1
# @date September 2020

import tkinter as tk
import numpy as np
from functools import partial
from time import sleep

# Buttons grid size, rows
panel_rows = 8
# Buttons grid size, columns
panel_cols = 14
# Number of images (shaded colors) a button can have
max_button_images = 8
# The size of the square buttons
button_size = 46
# The max number of fucntion groups (associated to the same number of
# button colors)
max_functions = max_button_images

# Creation of the root GUI
window = tk.Tk()
window.state('normal')
window.title('Py Synth Control panel')
window.background = 'black'

# A frame that includes all the buttons.
# The parameters for the border and pads will center the button grid
# on the screen. Keep them fixed! Should be recalculated if the
# button size or number of buttons change.
frame_container = tk.Frame(
    window,
    highlightcolor='black',
    highlightbackground='black',
    background="black",
    border=10,
    padx = 24,
    pady = 6
)

# Pack the frame container ready to include the buttons grid
frame_container.pack(
    side=tk.TOP,
    fill=tk.BOTH
)

# Buttons images list
# Every button can assume one of the images in the list, according
# to the applicaiton logic
# The button images are named accordingly, in the format b<nn>.png
b_images = list(tk.PhotoImage(file="images/b%02d.png" % (i+1)) for i in range(max_button_images))

# Default image when button is off
# (on action che image will change with one of the b_images list
image_off_button = tk.PhotoImage(file="images/bNull.png")

# Number of different function groups, corresponding to different
# button colors.
# The button zero (top left corner) changes the functions group
function_id = 0

# Buttons list
button = list()

# Debug flag. Set it to false to disable the debug messages
_debug = True

def get_button_id(row, col):
    '''
    Calculate the button id corresponding to the selected row and
    column in the panel grid

    Note that this mehod assumes that the buttons in the panel grid
    has been added to the buttons list following the row-by-row order
    and column-by-column

    :param row: the selected row
    :param col:  the selected column
    :return: the button id in the list
    '''
    return (row * panel_cols) + col

def klik(n):
    '''
    Button click callback function

    If the _debug flag is set to true, every time the top left
    button is pressed all the other buttons are set to the same color

    :param n: The ID of the clicked button
    '''
    global function_id

    # n not zero
    if (_debug):
        print("click: %d" % n)

    # When the top left button is pressed the colour is changed cyclically
    # Every color corresponds to a different set of features of the application
    if(n is 0):
        button[n].config(image=b_images[function_id])
        function_id += 1
        if(function_id is max_functions):
            function_id = 0

        # ---- Only for debug and testing
        if(_debug):
            print("click: %d" % n)
            for i in range(panel_rows):
                for j in range(panel_cols):
                    button[get_button_id(i, j)].config(image=b_images[function_id])
        # --- Debug end

def make_panel():
    '''
    Create the initial buttons panel in off state
    '''
    # Fill the buttons list with the objects
    for i in range(panel_rows):
        for j in range(panel_cols):
            button.append(
                tk.Button(frame_container,
                          image=image_off_button,
                          command=partial(klik, get_button_id(i, j))),
            )
            button[-1].grid(row=i, column=j)
            button[-1].activebackground='black'
            button[-1].height=button_size + 4
            button[-1].width=button_size + 4
            button[-1].border=2
            button[-1].background='black'
            button[-1].padx=6
            button[-1].pady=6
            button[-1].relief = 'flat'

if __name__ == "__main__":
    '''
    Main application
    '''
    make_panel()
    window.mainloop()