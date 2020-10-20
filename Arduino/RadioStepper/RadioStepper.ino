/**
 * @file RadioStepper.ino
 * @brief Software sketch to contorl a radio tuner with a stepper motor via a rotary encoder
 * with Arduino Nano.
 * 
 * @author Enrico Miglino <balearicdynamics@gmail.com>
 * @date July 2020 - October 2020
 * @version 1.0 Nano build 14 Release Candidate
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
  pinMode(PROG_LED, OUTPUT);
  // Start showing the LED activity
  blinkLEDPeriod(1500);
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
    encoderCounter = 0; // Reset che counter readings
    // Check for the direction (clockwise of conterclockwise)
    if (radioStepper.encValue == ROTARY_CW) {
      radioTuner.step(ONE_MOVE_CLOCKWISE);
      // Update the loop counter (only if programming is set)
      updateLoopCount(ONE_MOVE_CLOCKWISE);
    } // Clockwise rotation 
    else {
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
  #ifdef DEBUG
      Serial << "Encoder button clicked" << endl;
  #endif
    if(radioStepper.isSelected == false){
      radioStepper.isSelected = true;
      setProgrammingStatus(false);
      // LED fixed on
      digitalWrite(PROG_LED, HIGH);
#ifdef DEBUG
      Serial << "isSelected true" << endl;
#endif
    } // Button pressed for the first time: start programming the range
    else {
  #ifdef DEBUG
      Serial << "Set prog status true" << endl;
  #endif
      setProgrammingStatus(true);
    } // Programming ended, start looping
  } // Encoder button clicked

  // Check for looping
  if(radioStepper.isLooping == true) {
    radioStepper.tunerPosition += (STEPPER_INCREMENT * radioStepper.loopDirection);
    // Check if the direction should be inverted
    if( (radioStepper.tunerPosition == 0) || (radioStepper.tunerPosition == radioStepper.loopSteps) ) {
      radioStepper.loopDirection *= -1; // Invert the loop direction
    }
    radioTuner.step(STEPPER_INCREMENT * radioStepper.loopDirection);
  }
  
  // Non-blocking LED blinking, if needed
  blinkLEDOnce();
}

/**
 * IRQ Vector callback for Nano IRQ 0 (the loop control button pin)
 */
void irqLoopButton() {
  if(radioStepper.isProgrammed == true) {
    detachInterrupt(digitalPinToInterrupt(LOOPER_BUTTON));
     // If the tuner is programmed, change the status of the loop flag
    if(radioStepper.isLooping == true) {
      radioStepper.isLooping = false;
      radioStepper.blinkLEDFrequency = LED_IDLE;
#ifdef DEBUG
      Serial << "LED idle" << endl;
#endif
    } else {
      radioStepper.isLooping = true;
      radioStepper.blinkLEDFrequency = LED_FREQ;
#ifdef DEBUG
      Serial << "LED frequency" << endl;
#endif
    }
  attachInterrupt(digitalPinToInterrupt(LOOPER_BUTTON), irqLoopButton, LOW);
  delay(10);
  radioStepper.millisCounter = millis();
  }
}

/**
 * Change the radioStepper settings depending on
 * the program mode.
 * 
 * \param mode Enable or disable the programming mode
 */
 void setProgrammingStatus(boolean mode) {
  if(mode == true) {
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
      // Set the non-stopping blinking parameters
      // And initializes the timer.
      radioStepper.blinkLEDFrequency = LED_FREQ;
      radioStepper.millisCounter = millis();
  } else {
    //! Initializes the steps counter
    radioStepper.loopSteps = 0;
    // Disable the programming status
    radioStepper.isProgrammed = false;
    // Disable the looping mode
    radioStepper.isLooping = false;
    // LED off
    digitalWrite(PROG_LED, LOW);
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
  }
}

/**
 * Blink the signal LED once, inverting the status of the LED. This function should
 * be used during uninterruptable LED blinking.
 * 
 * The LED status is changed only if the right frequency time has passed else the function
 * do nothing.
 */
void blinkLEDOnce() {
  // Check if it is blink time
  if( ((millis() - radioStepper.millisCounter) >= radioStepper.blinkLEDFrequency) && radioStepper.isProgrammed) {
    // Invert the status of the LED
    if(radioStepper.isLEDOn) {
      digitalWrite(PROG_LED, LOW);
      radioStepper.isLEDOn = false;
    }
    else {
      digitalWrite(PROG_LED, HIGH);
      radioStepper.isLEDOn = true;
    }
    // Update the counter
    radioStepper.millisCounter = millis();
  }
}

/**
 * Blink the signal LED for a specified period (ms). If the period duration is
 * less than the frequency needed to blink twice, the function do nothing.
 * 
 * \param period The blink duration in ms
 */
void blinkLEDPeriod(int period) {
  // Check that the period is at least four times the blink frequency
  if(period / 2 >= LED_FREQ * 2) {
    //! The number of blinks (On/Off) of the LED
    int stepBlink = period / LED_FREQ;
    //! Blink loop
    int j;
    boolean isOn = true;

#ifdef DEBUG
    Serial << "blinkLEDPeriod(" << period << ") stepBlink " << stepBlink <<
              " Frequency " << LED_FREQ << endl;
#endif
    
    // Loop for the needed period
    for(j = 0; j < stepBlink; j++) {
      // Invert the last LED status and set the LED
      if(isOn) {
        digitalWrite(PROG_LED, HIGH);
        isOn = false;
      }
      else {
        digitalWrite(PROG_LED, LOW);
        isOn = true;
      }
      delay(LED_FREQ);
#ifdef DEBUG
      Serial << " " << isOn;
#endif
    }
    // Reset the LED to off
    digitalWrite(PROG_LED, LOW);
#ifdef DEBUG
    Serial << endl << " END." << endl;
#endif
  }
}
