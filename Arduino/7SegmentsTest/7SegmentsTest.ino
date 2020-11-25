
/**
 * @file 7SegmentsTest.ino
 * @brief Test the management of the 7 segments on the capacitor selector board.
 * 
 * This test loop the 7-segments LED display ignoring the rotary encoder and the rest
 * of the circuit connected to the Arduino. For testing purposes only
 * 
 * @author Enrico Miglino <balearicdynamics@gmail.com>
 * @date October 2020
 * @version 0.1
 */

#include <ShiftOutX.h>
#include <ShiftPinNo.h>
//#include <ShiftRegister595.h>
#include <Streaming.h>

//! Pin connected to ST_CP of 74HC595 pin 12
#define LATCH595 8    
//! Pin connected to SH_CP of 74HC595 pin 11
#define CLOCK595 12   
//! Pin connected to DS of 74HC595 pin 14
#define DATA595 11    

//! Undef this constant to interface a common cathode 7-segments LED display
#define COMMON_ANODE

//! Number of chained shift registers
#define CHAINED595 1

//! Undef this constant to enable the serial output debug
#undef DEBUG

/**
 * Defines the array with the 75HC595 pins to set for creating every number
 * 
 * @warning This version uses common anode (VCC) 7-segments LEDs so the segment is
 * On when the corresponding pin value of the shit register if set to Off. To give
 * easy compatibility of the software with both kinds of 7-segments display (common anode
 * or common cathode) the values are subtracted from 0xFF before sending the byte to the
 * shift register.
 */
#define DOT_7SEG 10

byte segments[11] = { 
    0x77,       // 0 
    0x14,       // 1
    0xB3,       // 2
    0xB6,       // 3
    0xD4,       // 4
    0xE6,       // 5
    0xE7,       // 6
    0x34,       // 7
    0xF7,       // 8
    0xF6,       // 9
    0x08        // Dot
    };

byte singleSeg[11] = { 
    0x01,       // 0 
    0x02,       // 1
    0x03,       // 2
    0x04,       // 3
    0x05,       // 4
    0x06,       // 5
    0x07,       // 6
    0x08,       // 7
    0x09,       // 8
    };

/** Creates the shiftOutX library instance with a single
 *  shift register (can be used up to 8 tested)
 *  
 *  @note Here se set the MSBFIRST as the first bit is the more significant.
 *  This means that the output bits order of the shift register is from
 *  pin Q0 to pin Q7 on the IC.
 */
shiftOutX regOne(LATCH595, DATA595, CLOCK595, MSBFIRST, CHAINED595); 

int SevenSegNum;
boolean SevenSegDot;

//! Initialization function
void setup() {
  #ifdef DEBUG
  Serial.begin(38400);
  #endif

  SevenSegDot = false;
  SevenSegNum = 0;
  update7Seg();
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

  SevenSegNum++;
  if(SevenSegNum > 9) {
    SevenSegNum = 0;
  }

  SevenSegDot = false;
  update7Seg();
  delay(2000);
//  SevenSegDot = true;
//  update7Seg();
//  delay(500);

//  update1Seg(SevenSegNum);
//  delay(1000);
}

//! Update the 7-segments LED display according to the number index of the array
//! If the bank selected flag is enabled, the dot is shown as well.
void update7Seg() {
  // Update the number on the display
  regOne.pinOff(0xFF);
  // Check for the Dot
  if(SevenSegDot == true) {
    regOne.pinOn(0xFF - (segments[SevenSegNum] + segments[DOT_7SEG]) );
  } else {
    regOne.pinOn(0xFF - segments[SevenSegNum] );
  }
}

//! Update a single 7-segments LED display
void update1Seg(int segment) {
  regOne.pinOff(0xFF);
  regOne.pinOn(0xFF - singleSeg[segment] );
}
