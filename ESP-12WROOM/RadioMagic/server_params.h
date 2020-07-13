/**
 * \file server_params.h
 * \brief Global parameters header to implement the web server and the software AP, 
 * as well as the REST commands
 * 
 * As the AP will connect to a single device sending commands to control the RadioMagic
 * synth, no special security is appplied to the connection. The access point default
 * IP address is 10.0.0.1:8081\n
 * All the commands are independent and correspond to a preset feature of the synth.
 * If the user - for example - set the weave or PWM mode on one of the three synths
 * also if it is disabled, the value is set anyway. When the synth is enabled, the 
 * mode is effective.\n
 * The web server lose the web control, all the settings are restored to the previous
 * manual settings.
 */

#ifndef _SERVER_PARAMS
#define _SERVER_PARAMS

//! AP SSID
#define SECRET_SSID "RadioMagic"
//! Password. Should be know by the remote client
#define SECRET_PASS "SynthControl"

//! https custom server port
#define SERVER_PORT 8081

//! Delay before the AP can connect the WiFi (ms)
#define AP_DELAY 10000

//! Server IP address
//! DO NOT USE with ESP32-WROOM by AZ Delivery !!! Hardware goes in reset loop
inline int IP(int x) { int ip[] = {10, 0, 0, 1}; return ip[x]; }
//! Acces Point IP gateway
//! DO NOT USE with ESP32-WROOM by AZ Delivery !!! Hardware goes in reset loop
inline int GATEWAY(int x) { int ip[] = {10, 0, 0, 1}; return ip[x]; }
//! Acces Point subnet
//! DO NOT USE with ESP32-WROOM by AZ Delivery !!! Hardware goes in reset loop
inline int SUBNET(int x) { int ip[] = {255, 255, 255, 0}; return ip[x]; }

//! HTTP GET Enable synth 1 \n
//! Parameter: 1 (true) or 0 (false) \n
//! Format: EnSynth1=[1,0]
#define HTTPGET_ENABLE_1     "/EnSynth1"

//! HTTP GET Enable synth 2 \n
//! Parameter: 2 (true) or 0 (false) \n
//! Format: EnSynth2=[1,0]
#define HTTPGET_ENABLE_2     "/EnSynth2"

//! HTTP GET Enable synth 3 \n
//! Parameter: 3 (true) or 0 (false) \n
//! Format: EnSynth3=[1,0]
#define HTTPGET_ENABLE_3     "/EnSynth3"

/**
 * Executes a stepper cycle from min to max number of steps.
 * 
 * If the digitally controlled radio tuning has not been programmed
 * before, this command has no effect.
 * 
 * Parameter: 1 (start tuning loop), 0 (stop tuning loop)\n
 * Format: Tune=[1,0]
 */
#define HTTPGET_TUNE          "/Tune"

//! Switch the synth 1 to wave or PWM mode\n
//! Parameter: 1 (wave mode) or 2 (PWM mode)
//! Format: WavePWM1=[1,2]
#define HTTPGET_WAVEPWM_1       "/WavePWM1"

//! Switch the synth 2 to wave or PWM mode\n
//! Parameter: 1 (wave mode) or 2 (PWM mode)
//! Format: WavePWM2=[1,2]
#define HTTPGET_WAVEPWM_2       "/WavePWM2"

//! Switch the synth 3 to wave or PWM mode\n
//! Parameter: 1 (wave mode) or 2 (PWM mode)
//! Format: WavePWM3=[1,2]
#define HTTPGET_WAVEPWM_3       "/WavePWM3"

//! Enable the sound output
//! Parameter: 1 (enable the sound) 0 (disable the sound)
//! Format: SoundOn=[1,0]
#define HTTPGET_SOUNDON         "/SoundOn"

/**
 * Enable the web controls of RadioMagic
 * 
 * The REST commands are executed in parallel though local switches
 * or the web. If the web control has not been enabled, the commands
 * has not effect. Until the web control is enabled, instead, the correspondin
 * manual controls are bypassed by the web commands.\n
 * To disable the web control it is sufficient to actuate one of the manual controls.
 * 
 * Parameter: 1 to pass the control to the remote client via WiFi or 0 to regain the
 * control to the physical switches.
 * Format: WebControl=[1,0]
 */
#define HTTPGET_WEBCONTROL      "/WebControl"

#endif
