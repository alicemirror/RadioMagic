/**
 * \file constants.h
 * \brief Constants and preset values
 */

// ==============================
//        Stepper Motor
// ==============================

#ifndef _CONSTANTS
#define _CONSTANTS

//! Steps per revolution, according to the motor specifications
#define STEPS_PER_REV 200
//! Preset tuner stepper speed
#define STEPPER_SPEED 90
//! Number of steps per increment.
#define STEPPER_INCREMENT 200
//! Stepper direction clockwise. The number of increments is multiplied
//! by the direction to get a positive or negative number
#define ROTATION_CW 1
//! Stepper direction counterclockwise. The number of increments is multiplied
//! by the direction to get a positive or negative number
#define ROTATION_CCW -1

//! Clockwise calculated steps
#define ONE_MOVE_CLOCKWISE STEPPER_INCREMENT * ROTATION_CW
//! Counterclockwise calculated steps
#define ONE_MOVE_COUNTERCLOCKWISE STEPPER_INCREMENT * ROTATION_CCW

//! L298 stepper motor contoller pin 1
#define STEPPER_PIN_1 8
//! L298 stepper motor contoller pin 2
#define STEPPER_PIN_2 9
//! L298 stepper motor contoller pin 3
#define STEPPER_PIN_3 10
//! L298 stepper motor contoller pin 4
#define STEPPER_PIN_4 11

// ==============================
//        Rotary Encoder
// ==============================

//! Rotary encoder button pin
#define ROTARY_BUTTON 3
//! Rotary encoder clock pin
#define ROTARY_CLK 6
//! Rotary encoder data pin
#define ROTARY_DATA 7
//! Rotary encoder value when rotating clockwise
#define ROTARY_CW -1
//! Rotary encoder value when rotating counterclockwise
#define ROTARY_CCW 1

//! Number of reading of the rotary encoder to take effect
//! Only the second reading is considered valid
#define ENCODER_READINGS 1

#endif
