import tkinter as tk
import numpy as np
from orbit import OrbitalSimulator  # Make sure this file is accessible

# Tkinter setup
root = tk.Tk()
root.title("Gravity Assist Simulator")
canvas_width = 800
canvas_height = 600
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="black")
canvas.pack()

side_panel = tk.Frame(root)
side_panel.pack(side=tk.RIGHT, fill=tk.Y)

ball_radius = 8  # Increased for visibility
planet_radius = 20
planetx = canvas_width / 2
planety = canvas_height / 2

# UI variables (dummy placeholders for now)
velocity_var1 = tk.DoubleVar(value=30000)
thrust_var1 = tk.DoubleVar(value=0)
mass_var = tk.DoubleVar(value=1000)
distance_var = tk.DoubleVar(value=7000)
planet_choice = tk.StringVar(value="Earth")
planet_values = {
    "Earth": {"M": 5.972e24, "r": 6.371e6},
    "Mars": {"M": 6.39e23, "r": 3.39e6},
    "Jupiter": {"M": 1.898e27, "r": 6.9911e7}
}

display_label = tk.Label(side_panel, text="", font=("consolas", 12), fg="white", bg="black")
display_label.pack(pady=10)

# Global animation state
animation_index = 0
animation_id = None
sim = None
ball = None

def scale_position(pos, canvas_width, canvas_height, center_offset=(0, 0), scale=2e-9):
    x = canvas_width / 2 + (pos[0] - center_offset[0]) * scale
    y = canvas_height / 2 - (pos[1] - center_offset[1]) * scale
    return x, y

def animate_simulated_path():
    global animation_index, ball, animation_id

    if animation_index < len(sim.trajectories['spacecraft']):
        pos = sim.trajectories['spacecraft'][animation_index]
        x, y = scale_position(pos, canvas_width, canvas_height, center_offset=sim.sun['pos'])

        canvas.coords(ball, x - ball_radius, y - ball_radius, x + ball_radius, y + ball_radius)
        canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="white", outline="")

        animation_index += 1
        animation_id = root.after(800, animate_simulated_path)

def run_animation():
    global sim, animation_index, ball

    sim = OrbitalSimulator()
    for _ in range(365):
        sim.update_bodies()

    animation_index = 0
    run_button.config(state=tk.DISABLED)

    canvas.delete("all")
    canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2, width=2, fill='#181BDF')

    global planet
    planet = canvas.create_oval(0, 0, 2 * planet_radius, 2 * planet_radius, fill="#181BDF")
    canvas.coords(planet, planetx - planet_radius, planety - planet_radius,
                  planetx + planet_radius, planety + planet_radius)

    ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")
    animate_simulated_path()

def reset_animation():
    global animation_id, animation_index, ball

    if animation_id:
        root.after_cancel(animation_id)
        animation_id = None

    canvas.delete("all")
    canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2, width=2, fill='#181BDF')

    global planet
    planet = canvas.create_oval(0, 0, 2 * planet_radius, 2 * planet_radius, fill="#181BDF")
    canvas.coords(planet, planetx - planet_radius, planety - planet_radius,
                  planetx + planet_radius, planety + planet_radius)

    x = 15
    y = canvas_height / 2
    ball = canvas.create_oval(x, y, x + 2 * ball_radius, y + 2 * ball_radius, fill="white")
    canvas.coords(ball, x, y, x + 2 * ball_radius, y + 2 * ball_radius)

    animation_index = 0
    display_label.config(text="")
    run_button.config(state=tk.NORMAL)

run_button = tk.Button(side_panel, text="Run Animation", command=run_animation,
                       font=("consolas bold", 12), bg="#D5D8DD", fg="#4D5D72")
run_button.pack(pady=10)

tk.Button(side_panel, text="Reset", command=reset_animation, font=("consolas bold", 12),
          bg="#D5D8DD", fg="#4D5D72").pack(pady=5)

root.mainloop()
