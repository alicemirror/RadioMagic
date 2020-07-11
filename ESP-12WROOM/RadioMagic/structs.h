/**
 * \file structs.h
 * \brief Status structures managed by the dual business logic of
 * the application, from the remote client or the physical switches
 * and buttons.
 */

#define SYNTH_MODE_WAVE true  ///< Synth is set to wave mode
#define SYNTH_MODE_PWM false  ///< Synth is set to PWM mode


 struct statusSynth {
  //! When true, the device is controlled by the remote client
  //! disabled on boot, the synth physical interface is the
  //! current controller
  boolean isControllling = true;
  //! The current synth mode. The default is overridden at boot reading the
  //! Status of the corresponding switch
  boolean modeSynth1 = SYNTH_MODE_WAVE;
  
 };
