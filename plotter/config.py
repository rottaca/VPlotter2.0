

PLOTTER_HARDWARE_CONFIG={
    "dir_pins"      : (22, 24),             # Direction GPIO pins for stepper driver
    "step_pins"     : (25, 23),             # Step GPIO pins for stepper driver
    "res_pins"      : (19, 13, 6),          # Resolution (microstepping) GPIO pins for stepper driver
    "invert_step_dir": (0, 0),              # Invert direction of stepper motors
    "micro_stepping": 16,                   # Microstepping for stepper drivers. Increases smoothness of movement but might slowdown drawing
    "servo_pin"     : 17,                   # Servo signal GPIO pin
    "servo_pos_up"  : 5,                    # Up position for servo (Duty cycle of PWM in ms)
    "servo_pos_down": 7,                    # Down position for servo (Duty cycle of PWM in ms)
    "base_width"    : 680,                  # Width of your plotter. Distance between left and right timing belt mount 
    "movement_resolution": 1,               # Sampling resolution for step computation in mm
    "steps_per_mm": 80                      # Steps per milimeter for stepper motors.
}
