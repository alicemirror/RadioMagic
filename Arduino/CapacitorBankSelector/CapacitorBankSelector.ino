/**
 * @file CapacitorBankSelector.ino
 * @brief Software sketch to contorl the rotary encoder and 7-segments LED display
 * for the Arduino Nano.
 * 
 * The role of the three Arduino Nano microcontrollers is to manage autonomously the
 * three sNE555-based synths frequency capacitors bank selection.
 * 
 * @author Enrico Miglino <balearicdynamics@gmail.com>
 * @date June 2020
 * @version 1.0
 */

#include <ShiftOutX.h>
#include <ShiftPinNo.h>
//#include <ShiftRegister595.h>
#include <Streaming.h>
#include <ClickEncoder.h>
#include <TimerOne.h>

//! Pin connected to ST_CP of 74HC595 pin 12
#define LATCH595 8    
//! Pin connected to SH_CP of 74HC595 pin 11
#define CLOCK595 12   
//! Pin connected to DS of 74HC595 pin 14
#define DATA595 11    
//! Rotary encoder button pin
#define ROTARY_BUTTON 5
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

//! Undef this constant to interface a common cathode 7-segments LED display
#define COMMON_ANODE

//! Number of chained shift registers
#define CHAINED595 1

//! Number of capacitors in the banck
#define NUM_CAPACITORS 6
//! Capacitor 1 control pin
#define CAP_1 2
//! Capacitor 2 control pin
#define CAP_2 3
//! Capacitor 3 control pin
#define CAP_3 4
//! Capacitor 4 control pin
#define CAP_4 9
//! Capacitor 5 control pin
#define CAP_5 10
//! Capacitor 6 control pin
#define CAP_6  13

//! Capacitors array pins assignement. The pins refers to the analog switch enable pin of the 
//! HEF4066B quad analog switch
int capArray[NUM_CAPACITORS] = { CAP_1, CAP_2, CAP_3, CAP_4, CAP_5, CAP_6 };

//! Undef this constant to eidable the serial output debug
#undef DEBUG

/**
 * Defines the array with the 75HC595 pins to set for creating every number
 * 
 * @note The Dot element should be added to the desired number when the
 * corresponding cpacitors bank has been selected.
 * 
 * @warning This version uses common anode (VCC) 7-segments LEDs so the a segment is
 * On when the corresponding pin value of the shit register if set to Off. To give
 * easy compaitibility of the software with both kinds of 7-segments display (common anode
 * or common cathode) the vales are subtracted from 0xFF before sending the byte to the
 * shift register.
 */
#define DOT_7SEG 10
byte segments[11] = { 
    0xB7,       // 0 
    0x14,       // 1
    0x73,       // 2
    0x76,       // 3
    0xD4,       // 4
    0xE6,       // 5
    0xE7,       // 6
    0x34,       // 7
    0xF7,       // 8
    0xF6,       // 9
    0x08        // Dot   
    };

/** Creates the shiftOutX library instance with a single
 *  shift register (can be used up to 8 tested)
 *  
 *  @note Here se set the MSBFIRST as the first bit is the more significant.
 *  This means that the output bits order of the shift register is from
 *  pin Q0 to pin Q7 on the IC.
 */
shiftOutX regOne(LATCH595, DATA595, CLOCK595, MSBFIRST, CHAINED595); 

//! Pointer to the ClickEncoder class
ClickEncoder *encoder;

//! Encoder interrupt service routine
void timerIsr() {
  encoder->service();
}

//! Bank selection parameters
struct BankSelect {
  //! Active bank number (0, no bank selected)
  int currentBank = 0;
  //! The shown bank is selected
  bool isSelected = false;
  //! Roatry encoder last position
  //! Current rotary encoder position
  int16_t encValue;
};

BankSelect bankCapacitors;

//! Initialization function
void setup() {
  #ifdef DEBUG
  Serial.begin(38400);
  #endif

  // Set the capacitors control pins and initially disabe all
  for(int j = 0; j < NUM_CAPACITORS; j++) {
    pinMode(capArray[j], OUTPUT);
  }
  disableAllCaps();

  encoder = new ClickEncoder(ROTARY_CLK, ROTARY_DATA, ROTARY_BUTTON);
  
  // Initialize the Rotary Encoder
  Timer1.initialize(1000);
  Timer1.attachInterrupt(timerIsr); 
  update7Seg(bankCapacitors.currentBank);
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
  bankCapacitors.encValue = encoder->getValue();

  // Check if the rotary postion has changed (exclude the zero status
  if ( (bankCapacitors.encValue != 0 ) && (encoderCounter == ENCODER_READINGS)) {
    // Disable the bank selection until the user does not press the rotary encoder button
    encoderCounter = 0; // Reset che counter readings
    bankCapacitors.isSelected = false;
    // Disable all the capacitors until a new one is not selected
    disableAllCaps();
    // Check for the direction (clockwise of conterclockwise)
    if (bankCapacitors.encValue == ROTARY_CW) {
      // Clockwise rotation, update the number by 1
      bankCapacitors.currentBank++;
      if(bankCapacitors.currentBank > NUM_CAPACITORS) {
        bankCapacitors.currentBank = 1;
      }
      #ifdef DEBUG
      Serial << "Clockwise rotation " << bankCapacitors.currentBank << endl;
      #endif
    } // Clockwise rotation 
    else {
      bankCapacitors.currentBank--;
      if(bankCapacitors.currentBank < 1) {
        bankCapacitors.currentBank = NUM_CAPACITORS;
        }
      #ifdef DEBUG
      Serial << "Counterclockwise rotation " << bankCapacitors.currentBank << endl;
      #endif
      } // Counterclockwise rotation
  update7Seg(bankCapacitors.currentBank);
  } // Rotary encoder has been moved twice
  else {
    if(bankCapacitors.encValue != 0){
      encoderCounter++;
        #ifdef DEBUG
        Serial << "First encoder reading" << endl;
        #endif
    }
  } // First encoder reading

  // Check for the rotary encoder button press. The 0 value shown on power-on can't be selected
  ClickEncoder::Button encButton = encoder->getButton();
  if( (encButton == ClickEncoder::Clicked) && 
      (bankCapacitors.isSelected == false) && 
      (bankCapacitors.currentBank > 0) ) {
    #ifdef DEBUG
    Serial << "BUTTON PRESSED " << endl;
    #endif
    bankCapacitors.isSelected = true;
    update7Seg(bankCapacitors.currentBank);
    enableCap(bankCapacitors.currentBank);
  }
}

//! Update the 7-segments LED display according to the number index of the array
//! If the bank selected flag is enabled, the dot is shown as well.
void update7Seg(int number) {
  // Update the number on the display
  regOne.pinOff(0xFF);
  // Check for the Dot
  if(bankCapacitors.isSelected == true) {
    regOne.pinOn(0xFF - (segments[bankCapacitors.currentBank] + segments[DOT_7SEG]) );
  } else {
    regOne.pinOn(0xFF - segments[bankCapacitors.currentBank] );
  }
}

//! Disable all the capacitors of the bank
void disableAllCaps() {
  for(int j = 0; j < NUM_CAPACITORS; j++) {
    digitalWrite(capArray[j], LOW);
  }
}

//! Enable the desired capacitor in the bank
//!
//! @note The capacitor is numbered starting from 1 (lower)
void enableCap(int capId) {
  disableAllCaps();
  digitalWrite(capArray[capId - 1], HIGH);
}
