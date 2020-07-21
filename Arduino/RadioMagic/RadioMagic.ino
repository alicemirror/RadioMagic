/**
  \file RadioMagic.ino
  \brief The Radio Magic Arduino MKR 1000 AP and web controller

  The program implement a dedicated access point and a restful web server
  to control some of the features of the Radio Magic hardware. This version
  control the BUSH FM/AM/AW transistor radio tuning via a stepper motor,
  the NE555 multi-synth interfacing some of the manual controls of the
  synth.

  \note This version has been originally developed for the ESP-32 WROOM by AZ Delivery module.\n
  Hardware WiFi library has an issue that avoid to set a dedicated ip address when
  setting the access point. This depends on the softAPConfig method that seems not
  working properly and continuously reset the hardware when a remote client tries to
  connect. Do not change the default WiFi AP IP address.\n
  The settings in the header file are still valid for other devices.
  A custom IP address for the AP (e.g. class 10.0.0.x) has been tested and works on
  the Arduino MKR1010 and MKR1000, as well as the ESP8266-12.\n
  Due to this and other issues, including the limitation of the power supply in the ESP-32
  and serious stability issues of the Stepper library, ths program has been moved by the version 1.1
  to the Arduino MKR1000 platform with minor updates, then some other improvements and
  changes to support all the project features, including the stepper motor control.

  \date July 2020
  \author Enrico Miglino <balearidcynamics@gmail.com>
  \version 1.1 build 12
 */

#include <Streaming.h>
#include <SPI.h>
#include <WiFi101.h>
#include <PCF8574.h>
#include <Stepper.h>
#include <ClickEncoder.h>

#include "server_params.h"
#include "log_strings.h"
#include "html_header.h"
#include "structs.h"
#include "constants.h"

//! #undef below to stop serial debugging info (speedup the system and reduces the memory)
#define _DEBUG

const char* ssid = SECRET_SSID;     ///< The WiFi SSID
const char* password = SECRET_PASS;  ///< The SSID password

//! Creates the server instance
WiFiServer server(SERVER_PORT);
//! Create the instance of the I2C GPIO extender (8 bits)
PCF8574 pcf8574(0x20, 21, 22);
//! initialize the stepper library
Stepper radioTuner(STEPS_PER_REV, STEPPER_PIN_1, 
                    STEPPER_PIN_2, STEPPER_PIN_3, 
                    STEPPER_PIN_4);
//! Pointer to the ClickEncoder class
ClickEncoder *encoder;
int16_t last, value;

void timerIsr() {
  encoder->service();
}

//! Number of steps, controlled by the encoder
int tunerIncrements = 0;

IPAddress local_IP(IP(0), IP(1), IP(2), IP(3));
IPAddress local_DNS(DNS(0), DNS(1), DNS(2), DNS(3));
IPAddress gateway(GATEWAY(0), GATEWAY(1), GATEWAY(2), GATEWAY(3));
IPAddress subnet(SUBNET(0), SUBNET(1), SUBNET(2), SUBNET(3));

//! Global status of the hardware device and controls.
StatusSynth hardware;

/** 
 *  Initialization function.
 *  
 *  In the setup funciton it is created the AP and assigned the default IP
 *  address, as well as the server creation. Only in debug mode (serial active)
 *  the setting operations are logged to the terminal.
 *  
 *  \note To manage the status when the AP can't be initializaed or there is a connection
 *  issue, the builting LED goes not to On
*/
void setup() {

#ifdef _DEBUG
  Serial.begin(38400);
  
  Serial << "RadioMagic Access Point Web Server\n" <<
            "Setting soft-AP configuration." << endl;
#endif

  // ------------------------------------------------
  // Initialize the 8574 pins
  // ------------------------------------------------
  pcf8574.pinMode(P0, OUTPUT, LOW);
  pcf8574.pinMode(P1, OUTPUT, HIGH);
  pcf8574.pinMode(P2, OUTPUT, LOW);
  pcf8574.pinMode(P3, OUTPUT, HIGH);
  pcf8574.pinMode(P4, OUTPUT, LOW);
  pcf8574.pinMode(P5, OUTPUT, HIGH);

  pcf8574.begin();

  // ------------------------------------------------
  // Initialize the tuner stepper speed
  // ------------------------------------------------
  radioTuner.setSpeed(STEPPER_SPEED);

  // ------------------------------------------------
  // Configure the AP and assign the SSID
  // ------------------------------------------------
  WiFi.config(local_IP, local_DNS, gateway, subnet);
  WiFi.beginAP(SECRET_SSID, SECRET_PASS);
  server.begin();

#ifdef _DEBUG 
  showWiFiStatus();
#endif

  // ------------------------------------------------
  // Initialize the rotary encoder
  // ------------------------------------------------
  // Initialize the rotary encoder button pin
  pinMode(ROTARY_BUTTON, INPUT);

  encoder = new ClickEncoder(ROTARY_CLK, ROTARY_DATA, ROTARY_BUTTON);
  
  last = -1;
}

//! Main appplication function.
void loop() {
  value += encoder->getValue();
  
  if (value != last) {
    last = value;
//    tunerIncrements = (int)(STEPPER_INCREMENT * value);
#ifdef _DEBUG
    Serial << "Rotary encoder moves tuner by " <<  value <<  " steps" << endl;
#endif
    radioTuner.step(tunerIncrements);
  }
  
  //! client contains the header when an incoming client
  //! is available
  WiFiClient client = server.available();   // listen for incoming clients
  // Check if the client is connected
  if (client) {
#ifdef _DEBUG
    Serial << "Client connected" << endl;
#endif
    //! String holding the data coming from the remote client
    String currentLine = "";

    // loop while the client's connected
    while (client.connected()) {
      // Check to ingoing bytes from the client.
      // Read bytes untile a newline is nor found
      if (client.available()) {
        char c = client.read();
        if (c == '\n') {
          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          if (currentLine.length() == 0) {
            // Generate the response page
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            String s = MAIN_page;
            client.println(s); //Send web page
            // break out of the while loop:
            break;
          } else {    // if you got a newline, then clear currentLine:
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // close the connection:
    client.stop();
    Serial.println("Client Disconnected.");
    }
  }

#ifdef _DEBUG
void showWiFiStatus() {
  Serial << "RadioMagic AP: " << SECRET_SSID << " (" << WiFi.localIP() << ")\n" << endl;
}
#endif

/**
 * Server response handler when the calling API does not exists
 * 
 * Generates an http 404 error
 */
void handleNotFound() {

//  String message = ERROR404;
//  message += "URI: ";
//  message += server.uri();
//  message += "\nMethod: ";
//  message += (server.method() == HTTP_GET) ? "GET" : "POST";
//  message += "\nArguments: ";
//  message += server.args();
//  message += "\n";
//  for (uint8_t i = 0; i < server.args(); i++) {
//    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
//  }
//  server.send(404, "text/plain", message);
}

/**
 * Server response when the calling API has some error
 * 
 * Generates an http 404 error without details. Only the
 * error code is shown
 */
void serverError(String apiErrorCode) {

  String message = ERROR404;
  message += apiErrorCode;
//  server.send(404, "text/plain", message);
}
