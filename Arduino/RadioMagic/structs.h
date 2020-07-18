/**
 * \file structs.h
 * \brief Status structures managed by the dual business logic of
 * the application, from the remote client or the physical switches
 * and buttons.
 */

#define SYNTH_MODE_WAVE true  ///< Synth is set to wave mode
#define SYNTH_MODE_PWM false  ///< Synth is set to PWM mode
#define SYNTH_ENABLED true    ///< Synth is enabled
#define SYNTH_DISABLED false  ///< Synth is disabled

/**
 * This structure defines the global status of the synthesizer switches
 * and settings.
 * 
 * When the server takes the control thre settings does not correspond to
 * the physical status of the switches. The status is restored rescanning
 * the physical controls when the server loose the control. Until the server
 * has the control, changing the status of the physical switches has no effect.
 */
struct StatusSynth {
  //! When true, the device is controlled by the remote client.
  //! Disabled on boot, the synth physical interface is the
  //! initial controller.
  boolean isRemoteControllling = true;
  //! The current synth 1 mode. The default is overridden at boot reading the
  //! status of the corresponding switch
  boolean modeSynth1 = SYNTH_MODE_WAVE;
  //! The current synth 2 mode. The default is overridden at boot reading the
  //! status of the corresponding switch
  boolean modeSynth2 = SYNTH_MODE_WAVE;
  //! The current synth 3 mode. The default is overridden at boot reading the
  //! status of the corresponding switch
  boolean modeSynth3 = SYNTH_MODE_WAVE;
  //! Enable/disable the synth 1. The default is overridden at boot reading the
  //! status of the corresponding switch.
  boolean enableSynth1 = SYNTH_ENABLED;
  //! Enable/disable the synth 2. The default is overridden at boot reading the
  //! status of the corresponding switch.
  boolean enableSynth2 = SYNTH_ENABLED;
  //! Enable/disable the synth 3. The default is overridden at boot reading the
  //! status of the corresponding switch.
  boolean enableSynth3 = SYNTH_ENABLED;
  //! When it is true, the BUSH radio tuner controlled by the stepper motor
  //! has been programmed and the tuning loop can run
  boolean isTunerProgrammed = false;
  //! Tuner min stepper value
  int minTunerSteps = 0;
  //! Tuner max stepper value
  int maxTunerSteps = 0;
 };
