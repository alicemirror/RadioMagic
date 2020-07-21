/**
 * @file RadioStepper.ino
 * @brief Software sketch to contorl radio tuner with a stepper motor via a rotary encoder
 * with Arduino Nano.
 * 
 * @author Enrico Miglino <balearicdynamics@gmail.com>
 * @date July2020
 * @version 1.0 Nano build 2
 */

#include <Streaming.h>
#include <ClickEncoder.h>
#include <TimerOne.h>
#include <Stepper.h>
#include "constants.h"

//! Undef this constant to eidable the serial output debug
#define DEBUG

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

//! Bank selection parameters
struct RadioStepper {
  //! The starting position has been selected
  bool isSelected = false;
  //! Roatry encoder last position
  //! Current rotary encoder position
  int16_t encValue;
};

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
    // Disable the bank selection until the user does not press the rotary encoder button
    encoderCounter = 0; // Reset che counter readings
    radioStepper.isSelected = false;
    // Check for the direction (clockwise of conterclockwise)
    if (radioStepper.encValue == ROTARY_CW) {
      #ifdef DEBUG
      Serial << "Clockwise rotation " << ONE_MOVE_CLOCKWISE << endl;
      #endif
      radioTuner.step(ONE_MOVE_CLOCKWISE);
    } // Clockwise rotation 
    else {
      #ifdef DEBUG
      Serial << "Counterclockwise rotation " << ONE_MOVE_COUNTERCLOCKWISE << endl;
      #endif
      radioTuner.step(ONE_MOVE_COUNTERCLOCKWISE);
      } // Counterclockwise rotation
  } // Rotary encoder has been moved twice
  else {
    if(radioStepper.encValue != 0){
      encoderCounter++;
        #ifdef DEBUG
        Serial << "First encoder reading, ignored." << endl;
        #endif
    }
  } // First encoder reading

  // Check for the rotary encoder button press. The 0 value shown on power-on can't be selected
  ClickEncoder::Button encButton = encoder->getButton();
  if( (encButton == ClickEncoder::Clicked) && 
      (radioStepper.isSelected == false) ) {
    #ifdef DEBUG
    Serial << "BUTTON PRESSED " << endl;
    #endif
    radioStepper.isSelected = true;
  }
}
