import tkinter as tk
from calculations import calculate_deflection_angle, calculate_velocity
import math

### CONSTANTS ###
G = 6.67430e-11 # Gravitational Constant
sim_time = 0.0
time_step = 0.016   # ~60 FPS

### BURN CONSTANTS ###
burn_applied = False
burn_time_start = None
burn_end_time = None

### PLANET VALUES (ACCURATE) (CHANGABLE) ###
# M = mass
# r = radius
planet_values_for_equations = {
    "Earth": {"M": 5.972e24, "r": 6.371e6},
    "Jupiter": {"M": 1.898e27, "r": 6.9911e7},
}

planet_gravity_scale = { # Scale works off of Earths values, change scale baased on differences in Earth to new planet
    "Earth": 0.1,    
    "Jupiter": 60.0,  
}

### SLIDER SETTINGS ###
planet_slider_settings = {
    "Earth":   {"v_min": 1000, "v_max": 50000,
                "t_min": 0, "t_max": 10000,
                "m_min": 1000, "m_max": 100000,
                "d_min": 7000, "d_max": 20000},

    "Jupiter": {"v_min": 1000, "v_max": 90000,
                "t_min": 0, "t_max": 30000,
                "m_min": 1000, "m_max": 200000,
                "d_min": 80000, "d_max": 1500000},
}

planet_visual_scale = { # Applied visual scale for graphic simplicity
    "Earth": 1.0,     # baseline
    "Jupiter": 2.0,   # spacecraft sits roughly twice as far visually
}

planet_colors = {
    "Earth": "#181BDF",   
    "Jupiter": "#E58E27"  
}


### WINDOW SETTINGS (DO NOT CHANGE) ###
root = tk.Tk()
root.title('Gravity Assist Sim')
root.geometry('1200x700')
root.resizable(False, False)

canvas_width = 1200 
canvas_height = 700

# Center on any screen #
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = int((screen_width / 2) - (canvas_width / 2))
y = int((screen_height / 2) - (canvas_height / 2))

root.geometry(f"{canvas_width}x{canvas_height}+{x}+{y}")
root.resizable(False, False)

# Conversion from real world values to fit on canvas values #
real_width_m = 100_000_000  # 100 million meters
real_height_m = 80_000_000  # 80 million meters

x_scale = canvas_width / real_width_m
y_scale = canvas_height / real_height_m

