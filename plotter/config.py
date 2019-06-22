

PLOTTER_CONFIG={
    # Stepper driver/motor configuration
    "dir_pins"      : (22, 24),             # Direction GPIO pins for stepper driver
    "step_pins"     : (25, 23),             # Step GPIO pins for stepper driver
    "res_pins"      : (19, 13, 6),          # Resolution (microstepping) GPIO pins for stepper driver
    "invert_step_dir": (0, 0),              # Invert direction of stepper motors
    "micro_stepping": 16,                   # Microstepping for stepper drivers. Increases smoothness of movement but might slowdown drawing
    "steps_per_mm": 80,                     # Steps per milimeter for stepper motors.

    # Servo configuration
    # The servo is controlled by GPIO.PWM with a frequency of 50 Hz
    # Specify up and down positions by setting the pulse width in percent
    # 100% = 1/50 s = 20 ms
    # Usually values are in range 1-2ms -> 5-10% 
    "servo_pin"     : 17,                   # Servo signal GPIO pin
    "servo_pos_up"  : 8.5,                  # Up position for servo (duty cycle in percent)
    "servo_pos_down": 7.5,                  # Down position for servo (duty cycle in percent)

    # Additional Hardware configuration
    "base_width"    : 680,                  # Width of your plotter. Distance between left and right timing belt mount

    # Drawing configuration
    "movement_resolution": 1.0              # Sampling resolution for step computation in mm, higher values decrease computational load but might also decrease quality

}
