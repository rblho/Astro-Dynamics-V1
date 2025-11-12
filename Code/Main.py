import tkinter as tk
import math
from calculations import calculate_deflection_angle, calculate_velocity

root = tk.Tk()
root.title("Curved Vector Turn")
root.state('zoomed')

canvas_width = root.winfo_screenwidth()
canvas_height = root.winfo_screenheight()

planetx = canvas_width / 2
planety = canvas_height / 2

canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="black")
canvas.pack()

ball_radius = 6
ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")

planet_radius = 100
planet = canvas.create_oval(0, 0, 2 * planet_radius, 2 * planet_radius, fill="pink")

canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2, width=2, fill='pink')


# Starting position
x = 0
y = canvas_height / 1.5

r = ball_radius
pr = planet_radius

canvas.coords(ball, x - r, y - r, x + r, y + r)
canvas.coords(planet, planetx - pr, planety - pr, planetx + pr, planety + pr)


#### Inputs for the simulation ####

### JUPITER ###
# v_i = 35000      # m/s
# d = 3.5018e8      # m
# M_s = 721.9       # kg
# T = 5000         # N
# burn_active = False
# ################

# # ### EARTH ###
# v_i = 0   # m/s
# d = 70000.0        # m
# M_s = 1000       # kg
# T = 0         # N
# burn_active = False
# ###############

# Compute final velocity and deflection angle
vel_msg, vf_total = calculate_velocity(v_i, d, M_s, T, burn_active)
angle_deg = calculate_deflection_angle(vf_total, d)

print(vel_msg)
print(f"Deflection angle: {angle_deg:.3f}°")

#############################################################


# Parameters
step = 5
straight_distance = 720  # pixels before curve
turn_angle_deg = angle_deg      # angle to curve into
curve_steps = 50        # number of frames to complete the curve

# Internal state
distance_traveled = 0
vx = step
vy = 0
curve_index = 0
curve_path = []

def move_straight():
    global x, y, distance_traveled
    x += vx
    y += vy
    canvas.coords(ball, x - r, y - r, x + r, y + r)
    canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="white", outline="")
    distance_traveled += step
    if distance_traveled >= straight_distance:
        prepare_curve()
    else:
        root.after(16, move_straight)

def prepare_curve():
    global curve_path
    angle_rad = math.radians(turn_angle_deg)
    for i in range(curve_steps + 1):
        t = i / curve_steps 
        theta = t * angle_rad
        vx_rot = step * math.cos(theta)
        vy_rot = -step * math.sin(theta)
        curve_path.append((vx_rot, vy_rot))
    move_curve()

def move_curve():
    global x, y, curve_index
    if curve_index < len(curve_path):
        vx, vy = curve_path[curve_index]
        x += vx
        y += vy
        canvas.coords(ball, x - r, y - r, x + r, y + r)
        canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="white", outline="")
        curve_index += 1
        root.after(16, move_curve)
    else:
        continue_straight()

def continue_straight():
    angle_rad = math.radians(turn_angle_deg)
    vx = step * math.cos(angle_rad)
    vy = -step * math.sin(angle_rad)
    def move_out():
        global x, y
        x += vx
        y += vy
        canvas.coords(ball, x - r, y - r, x + r, y + r)
        canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="white", outline="")
        root.after(16, move_out)
    move_out()

        
    

move_straight()
root.mainloop()
