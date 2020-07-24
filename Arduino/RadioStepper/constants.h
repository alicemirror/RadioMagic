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
//! Number of steps per increment, corresponding to a rotary encoder
//! single step.
#define STEPPER_INCREMENT 100
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

//! Rotary encoder button pin (attached to Nano IRQ1)
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

// ==============================
//        Looper Button
// ==============================

//! Rotary encoder button pin (attached to Nano IRQ0)
#define LOOPER_BUTTON 2

// ==============================
//        Status Struct
// ==============================

/**
 * The RadioStepper structure contains the status of
 * all the parameters controlling the behavior of the radio
 */
struct RadioStepper {
  /** 
   * The starting position has been selected 
   * 
   * This happens when the user press for the first
   * time the rotary encoder button. From that point,
   * the number of effective steps is counted until
   * the button is not pressed for the second time.
   */
  bool isSelected = false;
  /**
   * When the button has been pressed for the second time, the 
   * programmed status indicates that the system is ready to 
   * loop the tuner.
   */
  bool isProgrammed = false;
  //! Status enabled when the tuner is looping
  bool isLooping = false;
  //! Current relative tuner position inside a loop
  int tunerPosition = 0;
  //! Looping direction. It is inverted when one of the two limits
  //! is reached
  int loopDirection = 0;
  /**
   * Steps units expressed in number of rotary pulses
   * 
   * The units are added algebraically to the counter until
   * the rotary encoder button is not pressed for the second
   * time. At this point the controller is programmed to execute
   * a loop.
   */
  int loopSteps = 0;
  //! Current rotary encoder position
  int16_t encValue = 0;
};

#endif
