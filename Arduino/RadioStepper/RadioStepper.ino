/**
 * @file RadioStepper.ino
 * @brief Software sketch to contorl a radio tuner with a stepper motor via a rotary encoder
 * with Arduino Nano.
 * 
 * @author Enrico Miglino <balearicdynamics@gmail.com>
 * @date July 2020
 * @version 1.0 Nano build 10
 */

#include <Streaming.h>
#include <ClickEncoder.h>
#include <TimerOne.h>
#include <Stepper.h>
#include "constants.h"

//! Undef this constant to enable the serial debug
#undef DEBUG

//! Pointer to the ClickEncoder class
ClickEncoder *encoder;
//! initialize the stepper library
Stepper radioTuner(STEPS_PER_REV, STEPPER_PIN_1, 
                    STEPPER_PIN_2, STEPPER_PIN_3, 
                    STEPPER_PIN_4);

//! Encoder interrupt service routine
void timerIsr() {
  encoder->service();
}

RadioStepper radioStepper;

//! Initialization function
void setup() {
  #ifdef DEBUG
  Serial.begin(38400);
  #endif
  
  // ------------------------------------------------
  // Initialize the tuner stepper speed
  // ------------------------------------------------
  radioTuner.setSpeed(STEPPER_SPEED);

  // ------------------------------------------------
  // Initialize the rotary encoder
  // ------------------------------------------------
  encoder = new ClickEncoder(ROTARY_CLK, ROTARY_DATA, ROTARY_BUTTON);
  
  // Initialize the Rotary Encoder
  Timer1.initialize(1000);
  Timer1.attachInterrupt(timerIsr); 

  // ------------------------------------------------
  // Enable the loop control interrupt button
  // ------------------------------------------------
  pinMode(LOOPER_BUTTON, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(LOOPER_BUTTON), irqLoopButton, LOW);
}

/** 
 * Main loop function 
 * 
 * @note The rotary counter should be read twice before the number is incremented
 * due to the mechanical characterisics of the device: it is difficult to positio
 * the encoder in the intermediate positionl
 */
int encoderCounter = 0;

void loop() {
  // Read the encoder value. Maybe -1, 1 or 0
  radioStepper.encValue = encoder->getValue();

  // Check if the rotary postion has changed (exclude the zero status
  if ( (radioStepper.encValue != 0 ) && (encoderCounter == ENCODER_READINGS)) {
    if(radioStepper.isProgrammed == true) {
      // If the tuner is programmed and the user moves the rotary encoder
      // the programmed status is automatically reset
      setProgrammingStatus(false);
    }
    // Disable the bank selection until the user does not press the rotary encoder button
    encoderCounter = 0; // Reset che counter readings
    // Check for the direction (clockwise of conterclockwise)
    if (radioStepper.encValue == ROTARY_CW) {
      #ifdef DEBUG
      Serial << "Clockwise rotation " << ONE_MOVE_CLOCKWISE << endl;
      #endif
      radioTuner.step(ONE_MOVE_CLOCKWISE);
      // Update the loop counter (only if programming is set)
      updateLoopCount(ONE_MOVE_CLOCKWISE);
    } // Clockwise rotation 
    else {
      #ifdef DEBUG
      Serial << "Counterclockwise rotation " << ONE_MOVE_COUNTERCLOCKWISE << endl;
      #endif
      radioTuner.step(ONE_MOVE_COUNTERCLOCKWISE);
      // Update the loop counter (only if programming is set)
      updateLoopCount(ONE_MOVE_COUNTERCLOCKWISE);
      } // Counterclockwise rotation
  } // Rotary encoder has been moved twice
  else {
    if(radioStepper.encValue != 0){
      encoderCounter++;
    }
  } // First encoder reading

  // Check for the rotary encoder button press. The 0 value shown on power-on can't be selected
  ClickEncoder::Button encButton = encoder->getButton();
  if(encButton == ClickEncoder::Clicked) {
    if(radioStepper.isSelected == false){
    radioStepper.isSelected = true;
    setProgrammingStatus(false);
    #ifdef DEBUG
    Serial << "Start freq. range programming" << endl;
    #endif
    } // Button pressed for the first time: start programming the range
    else {
      setProgrammingStatus(true);
    } // Button pressed for the second time. Programming ended.
  }

  // Check for looping
  if(radioStepper.isLooping == true) {
    radioStepper.tunerPosition += (STEPPER_INCREMENT * radioStepper.loopDirection);
    // Check if the direction should be inverted
    if( (radioStepper.tunerPosition == 0) || (radioStepper.tunerPosition == radioStepper.loopSteps) ) {
      radioStepper.loopDirection *= -1; // Invert the loop direction
    }
    radioTuner.step(STEPPER_INCREMENT * radioStepper.loopDirection);
    #ifdef DEBUG
    Serial << "Current stepper position " << radioStepper.tunerPosition << endl;
    #endif
  }
}

/**
 * IRQ Vector callback for Nano IRQ 0 (the loop control button pin)
 */
void irqLoopButton() {
  if(radioStepper.isProgrammed == true) {
    // If the tuner is programmed, change the status of the loop flag
    if(radioStepper.isLooping == true) {
      radioStepper.isLooping = false;
    } else {
      radioStepper.isLooping = true;
    }
  }
}

/**
 * Change the radioStepper settings depending on
 * the program mode.
 * 
 * \param mode Enable or diable the programming mode
 */
 void setProgrammingStatus(boolean mode) {
  if(mode == true) {
      #ifdef DEBUG
      Serial << "End prog. Tuner loops " << radioStepper.loopSteps <<
                " steps in both directions" << endl;
      #endif
      // reset the programming selection status for the next cycle
      radioStepper.isSelected = false;
      radioStepper.isProgrammed = true;
      // Set the starting point to the last position reached while programming
      radioStepper.tunerPosition = radioStepper.loopSteps;
      // Enable the looping mode (temporary for testing only)
      radioStepper.isLooping = true;
      if(radioStepper.loopSteps > 0) {
        // Start decreasing the tuner position
        radioStepper.loopDirection = ROTATION_CCW;
      } else {
        // Start increasing the tuner position
        radioStepper.loopDirection = ROTATION_CW;
      }
  } else {
      #ifdef DEBUG
      Serial << "Prog mode off" << endl;
      #endif
    //! Initializes the steps counter
    radioStepper.loopSteps = 0;
    // Disable the programming status
    radioStepper.isProgrammed = false;
    // Disable the looping mode
    radioStepper.isLooping = false;
  }
 }

/**
 * Update the steps loop count according to the 
 * rotary encoder direction.
 * 
 * The counter is updated only when the system is 
 * in programming mode.
 * 
 * \param dir The number of steps, positive or negative.
 */
 void updateLoopCount(int dir) {
  if(radioStepper.isSelected == true) {
    radioStepper.loopSteps += dir;
    #ifdef DEBUG
    Serial << "Update the loop counter to " << radioStepper.loopSteps << endl;
    #endif
  }
}
