import tkinter as tk
from calculations import calculate_deflection_angle, calculate_velocity
import math
from PIL import Image, ImageTk

G = 6.67430e-11  # gravitational constant
M_p = 5.972e24   # mass of planet (Earth-like)

burn_applied = False
burn_start_time = None
burn_end_time = None


simulation_time = 0.0  # seconds
time_step = 0.016      # assuming ~60 FPS


planet_values = {
    "Earth": {"M": 5.972e24, "r": 6.371e6},
    "Jupiter": {"M": 1.898e27, "r": 6.9911e7},
    "Mars": {"M": 6.417e23, "r": 3.3895e6},
    "Venus": {"M": 4.867e24, "r": 6.0518e6}
}

root = tk.Tk()
root.title('AstroDynamics')
root.state('zoomed')

canvas_width = root.winfo_screenwidth()
canvas_height = root.winfo_screenheight()

# --- Real-world to canvas conversion ---
real_width_m = 100_000_000  # 100 million meters
real_height_m = 80_000_000  # 80 million meters

x_scale = canvas_width / real_width_m
y_scale = canvas_height / real_height_m

def draw_diagram(canvas):
    # --- Draw two straight lines ---
    canvas.create_line((canvas_width / 2) - 125, canvas_height/2 + 100, (canvas_width / 2) - 125, canvas_height/2, fill="#8BB9F4", width=4) # Vertical line
    canvas.create_line((canvas_width / 2) - 55, canvas_height/2 + 85,(canvas_width / 2) - 120, canvas_height/2,fill="#FB8246", width=4)
    vf_ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")
    vf_r = 5
    vf_x = (canvas_width / 2) - 1 
    vf_y = (canvas_height / 2) - 6

    canvas.coords(vf_ball, vf_x - vf_r, vf_y - vf_r, vf_x + vf_r, vf_y + vf_r)
    canvas.tag_raise(vf_ball)

    # --- Draw five text boxes ---
    box_coords = [
        ((canvas_width / 2) - 170, canvas_height/2 + 65, "d"),
        ((canvas_width / 2) - 120, canvas_height/2 + 45, "θ°"),
        ((canvas_width / 2) - 32 ,(canvas_height / 2) - 35, "Vf"),
        ((canvas_width - canvas_width) + 10 ,(canvas_height / 2) + 65, "Vi(r=∞)"),
        ((canvas_width / 2) + 400, canvas_height/2 - 300, "Vf(r=∞)")
    ]

    for x, y, label in box_coords:
        canvas.create_text(x + 30, y + 15, text=label, font=("consolas bold", 12), fill="White", anchor="center")



def to_real_coords(x_px, y_px):
    """
    Convert canvas coordinates (pixels) back into real-world coordinates (meters)
    """
    x_m = x_px / x_scale
    y_m = y_px / y_scale
    return x_m, y_m

def flash_burn_effect():
    """Temporarily turn the spacecraft red for 2 seconds after a burn."""
    try:
        canvas.itemconfig(ball, fill="red")
        # Return to white after 2 seconds (2000 ms)
        root.after(2000, lambda: canvas.itemconfig(ball, fill="white"))
    except:
        pass  

class ToolTip:
    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tipwindow = None

    def showtip(self, x, y):
        if self.tipwindow or not self.text.strip():
            return
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x+15}+{y+10}")
        label = tk.Label(
            tw, text=self.text, bg="#333333", fg="white",
            font=("consolas", 10), relief=tk.SOLID, borderwidth=1
        )
        label.pack(ipadx=4, ipady=2)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None





main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

side_panel = tk.Frame(main_frame, width=300, bg='#4D5D72')
side_panel.pack(side=tk.RIGHT, fill=tk.Y)
side_panel.pack_propagate(False)

canvas = tk.Canvas(main_frame, width=canvas_width, height=canvas_height, bg="black")
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

planet_choice = tk.StringVar(value="Earth")
planet_menu = tk.OptionMenu(canvas, planet_choice, *planet_values.keys())
planet_menu.config(font=("consolas", 10), bg="#D5D8DD", fg="#4D5D72", highlightthickness=0)
planet_menu.place(x=20, y=20)

planetx = canvas_width / 2 - 125
planety = canvas_height / 2
ball_radius = 4
planet_radius = 60



# --- Burn points storage ---
burn_records = []

show_burn_dots_var = tk.BooleanVar(value=False)


def draw_burn_dots():
    """Draws burn dots with tooltips showing burn info."""
    canvas.delete("burn_dot")

    if show_burn_dots_var.get():
        for i, record in enumerate(burn_records):
            x_m, y_m = record["coords"]
            x_px = x_m * x_scale
            y_px = y_m * y_scale

            dot_color = "#FF0000" if record["time"] else "#AA3333"  # darker if pending
            dot = canvas.create_oval(
                x_px - ball_radius, y_px - ball_radius,
                x_px + ball_radius, y_px + ball_radius,
                fill=dot_color, outline="", tags=("burn_dot", f"dot_{i}")
            )

            if record["time"] is not None:
                tt_text = (f"Burn time: {record['time']:.2f} s\n"
                           f"Final velocity: {record['velocity']:.2f} m/s")
            else:
                tt_text = "Pending burn"

            tooltip = ToolTip(canvas, text=tt_text)

            def on_enter(event, tt=tooltip):
                tt.showtip(event.x_root, event.y_root)
            def on_leave(event, tt=tooltip):
                tt.hidetip()

            canvas.tag_bind(f"dot_{i}", "<Enter>", on_enter)
            canvas.tag_bind(f"dot_{i}", "<Leave>", on_leave)



velocity_var1 = tk.IntVar(value=0)
thrust_var1 = tk.IntVar(value=0)
mass_var = tk.IntVar(value=1000)
distance_var = tk.DoubleVar(value=7000)

draw_diagram(canvas)

global ball
animation_id = None
animation_ids = []

ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")
initial_d_km = distance_var.get()
normalized = (initial_d_km - 7000) / (50000 - 7000)
ball_start_y = canvas_height * (0.60 + normalized * 0.06)
x = 14
y = ball_start_y + 9
canvas.coords(ball, x, y, x + 2 * ball_radius, y + 2 * ball_radius)

planet = canvas.create_oval(0, 0, 2 * planet_radius, 2 * planet_radius, fill="#181BDF")

# --- Load the image once (keep a global reference so it doesn’t disappear) ---
earth_photo = tk.PhotoImage(file="earttt.png")
earth_small = earth_photo.subsample(3, 3)  # adjust scale as needed

# --- Draw image centered above the existing oval ---
planet_img_id = canvas.create_image(
    planetx, planety, image=earth_small, anchor="center", tags="planet_image"
)
canvas.tag_raise("planet_image", planet)  # ensure image is on top

canvas.coords(planet, planetx - planet_radius, planety - planet_radius,
              planetx + planet_radius, planety + planet_radius)
canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2, width=2, fill='#1702ae')

canvas.tag_raise("planet_image")


label = tk.Label(side_panel, text="Controls", fg="#4D5D72", bg="#D5D8DD", font=("consolas bold", 14))
label.pack(pady=20)

slider_frame = tk.Frame(side_panel, bg='#4D5D72')
slider_frame.pack(pady=10)
slider_frame.grid_columnconfigure(1, minsize=30)


def update_velocity1(val): velocity_var1.set(int(float(val)))
def update_thrust1(val): thrust_var1.set(int(float(val)))
def update_mass(val): mass_var.set(int(float(val)))

def update_spacecraft_position(val):
    d_km = float(val)
    normalized = (d_km - 7000) / (50000 - 7000)
    ball_start_y = canvas_height * (0.60 + normalized * 0.06)
    x = 15
    y = ball_start_y
    canvas.coords(ball, x, y, x + 2 * ball_radius, y + 2 * ball_radius)
    distance_var.set(d_km)


example_line = canvas.create_line(
    20, planety + 100,
    planetx - 5, planety + 100,
    width=2, fill="white", dash=(5, 5), tags="trajectory_line"
)


x_end = planetx - 5
y_end = planety + 100
points = [
    x_end, y_end,
    x_end + 105, y_end + 5,
    x_end + 130, y_end - 100
]
curve_line = canvas.create_line(points, fill="white", width=2, smooth=True, dash=(5, 5), tags="trajectory_line")

click_used = False
clicked_coord = None

click_ball = None 

def on_line_click(event):
    global click_used, clicked_coord, click_ball

    if click_used:
        return

    thrust_slider1.config(state="normal")
    thrust_entry1.config(state="normal")

    clicked_items = canvas.find_withtag("current")
    for item in clicked_items:
        if "trajectory_line" in canvas.gettags(item):
            # Convert and store real-world coordinates
            x_m, y_m = to_real_coords(event.x, event.y)
            clicked_coord = (x_m, y_m)

            burn_records.append({
                "coords": (x_m, y_m),
                "time": None,
                "velocity": None
            })
            print(f"Saved burn record #{len(burn_records)}: ({x_m:.2f}, {y_m:.2f})")

            # --- visual marker ---
            if click_ball:
                canvas.delete(click_ball)
            click_ball = canvas.create_oval(
                event.x - ball_radius, event.y - ball_radius,
                event.x + ball_radius, event.y + ball_radius,
                fill="#AA3333"  # darker red = pending
            )

            click_used = True
            draw_burn_dots()



canvas.tag_bind("trajectory_line", "<Button-1>", on_line_click)

# --- Sliders and entries ---
tk.Label(slider_frame, text="Velocity (m/s)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=0, column=0, pady=(0, 5))
velocity_slider1 = tk.Scale(slider_frame, from_=50000, to=0, orient=tk.VERTICAL, length=150,
                            fg="white", bg="#4D5D72", troughcolor="#4D5D72",
                            highlightthickness=0, command=update_velocity1)
velocity_slider1.grid(row=1, column=0)
velocity_entry1 = tk.Entry(slider_frame, textvariable=velocity_var1, width=10, justify='center')
velocity_entry1.grid(row=2, column=0, pady=(5, 10))
velocity_var1.trace_add("write", lambda *args: velocity_slider1.set(velocity_var1.get()))

tk.Label(slider_frame, text="Thrust (N)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=0, column=2, pady=(0, 5))
thrust_slider1 = tk.Scale(slider_frame, from_=10000, to=0, orient=tk.VERTICAL, length=150,
                          fg="white", bg="#4D5D72", troughcolor="#4D5D72",
                          highlightthickness=0, command=update_thrust1)
thrust_slider1.grid(row=1, column=2)
thrust_entry1 = tk.Entry(slider_frame, textvariable=thrust_var1, width=10, justify='center')
thrust_entry1.grid(row=2, column=2, pady=(5, 10))
thrust_var1.trace_add("write", lambda *args: thrust_slider1.set(thrust_var1.get()))

thrust_slider1.config(state="disabled")
thrust_entry1.config(state="disabled")

tk.Label(slider_frame, text="SpaceCraft Mass (kg)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=3, column=0, pady=(0, 5))
mass_slider = tk.Scale(slider_frame, from_=100000, to=1000, orient=tk.VERTICAL, length=150,
                       fg="white", bg="#4D5D72", troughcolor="#4D5D72",
                       highlightthickness=0, command=update_mass)
mass_slider.grid(row=4, column=0)
mass_entry = tk.Entry(slider_frame, textvariable=mass_var, width=10, justify='center')
mass_entry.grid(row=5, column=0, pady=(5, 10))
mass_var.trace_add("write", lambda *args: mass_slider.set(mass_var.get()))

tk.Label(slider_frame, text="Distance (km)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=3, column=2, pady=(0, 5))
distance_slider = tk.Scale(slider_frame, from_=50000, to=7000, resolution=10,
                           orient=tk.VERTICAL, length=150, fg="white", bg="#4D5D72",
                           troughcolor="#4D5D72", highlightthickness=0,
                           command=update_spacecraft_position)
distance_slider.grid(row=4, column=2)
distance_entry = tk.Entry(slider_frame, textvariable=distance_var, width=10, justify='center')
distance_entry.grid(row=5, column=2, pady=(5, 10))
distance_var.trace_add("write", lambda *args: distance_slider.set(distance_var.get()))

# --- Spacer below sliders ---
tk.Label(slider_frame, text="", bg="#4D5D72").grid(row=6, column=0, columnspan=3, pady=5)


# --- Compact timers below sliders ---
timer_frame = tk.Frame(slider_frame, bg="#4D5D72")
timer_frame.grid(row=8, column=0, columnspan=3, pady=(4, 4))

time_label = tk.Label(timer_frame, text="Time: 0.00 s",
                      font=("consolas", 10), fg="white", bg="#3B4148")
time_label.pack(side="left", padx=(0, 10))

burn_time_label = tk.Label(timer_frame, text="Burn Time: -- s",
                           font=("consolas", 10), fg="white", bg="#3B4148")
burn_time_label.pack(side="left")

# --- Ultra-compact "Show Burn Dots" toggle ---
show_burn_dots_var = tk.BooleanVar(value=False)
show_burn_dots_check = tk.Checkbutton(
    side_panel,
    text="Show Burn Dots",
    variable=show_burn_dots_var,
    command=draw_burn_dots,
    font=("consolas", 8),
    bg="#4D5D72",
    fg="white",
    selectcolor="#4D5D72",
    activebackground="#4D5D72",
    highlightthickness=0,
    borderwidth=0,
    padx=0,
    pady=0
)

# Pack it snugly just under the timer section
show_burn_dots_check.pack(pady=(0, 0), anchor="center")

result_label = tk.Label(side_panel, text="", fg="white", bg="#4D5D72", font=("consolas", 10))
result_label.pack(pady=10)

display_frame = tk.Frame(side_panel, bg="#D5D8DD", bd=5, relief=tk.SUNKEN)
display_frame.pack(pady=10, padx=10, fill=tk.X)
display_label = tk.Label(display_frame, text=f"v_final = \nv_infinity = \nDeflection angle = ",
                         justify="left", anchor="w", bg="#D5D8DD", fg="#4D5D72",
                         font=("consolas", 11))
display_label.pack(padx=10, pady=10, anchor="w")

# --- All original functions included below ---

def run_animation():
    global x, y, r, pr, vx, vy, curve_index, curve_path, turn_angle_deg, distance_traveled
    run_button.config(state=tk.DISABLED)
    show_burn_dots_check.config(state=tk.DISABLED)
    show_burn_dots_var.set(False)
    draw_burn_dots()  # clears the dots if visible


    canvas.delete("example_line")
    canvas.delete("all")
    canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2, width=2, fill='#181BDF')
    global ball
    ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")
    planet = canvas.create_oval(0, 0, 2 * planet_radius, 2 * planet_radius, fill="#181BDF")
    canvas.coords(planet, planetx - planet_radius, planety - planet_radius,
                  planetx + planet_radius, planety + planet_radius)
    v_i = velocity_var1.get()
    T = thrust_var1.get()
    M_s = mass_var.get()
    d_km = distance_var.get()
    d_m = d_km * 1000
    burn_active = True
    selected_planet = planet_choice.get()
    M = planet_values[selected_planet]["M"]
    r = planet_values[selected_planet]["r"]
    vel_msg, vf_total, v_inf = calculate_velocity(v_i, d_m, M_s, T, burn_active, M, r)

    thrust_slider1.config(state="disabled")
    thrust_entry1.config(state="disabled")

    velocity_slider1.config(state="disabled")
    velocity_entry1.config(state="disabled")

    distance_slider.config(state="disabled")
    distance_entry.config(state="disabled")

    mass_slider.config(state="disabled")
    mass_entry.config(state="disabled")

    
    angle_deg = calculate_deflection_angle(vf_total, d_m, M)
    display_label.config(text=f"v_final = {vf_total:.2f} m/s\nv_infinity = {v_inf:.2f} m/s\nDeflection angle = {angle_deg:.2f}°")
    normalized = (d_km - 7000) / (50000 - 7000)
    ball_start_y = canvas_height * (0.590 + normalized * 0.4)
    x = 0
    y = ball_start_y
    r = ball_radius
    pr = planet_radius
    global vx, vy
    vx = 3
    vy = 0
    curve_index = 0
    curve_path = []
    turn_angle_deg = min(angle_deg, 120)
    global curve_trigger_distance
    if turn_angle_deg > 100:
        curve_trigger_distance = 640 + (turn_angle_deg - 100) * 2
    else:
        curve_trigger_distance = 640 
    distance_traveled = 0
    canvas.coords(ball, x, y, x + 2 * ball_radius, y + 2 * ball_radius)
    move_straight()


time_step = 0.016  # seconds per frame (~60 FPS)
simulation_time = 0.0

def move_straight():
    global x, y, vx, vy, distance_traveled, burn_applied, simulation_time, ball_radius

    # Increment time
    simulation_time += time_step
    time_label.config(text=f"Time: {simulation_time:.2f} s")

    # Gravitational acceleration
    dx = planetx - x
    dy = planety - y
    r_squared = dx**2 + dy**2
    r = math.sqrt(r_squared)
    if r_squared > 0:
        F = G * M_p / r_squared
        F = F / 1e13 * 2
        ax = F * dx / r
        ay = F * dy / r
        vx += ax
        vy += ay

    # Update position
    x += vx
    y += vy
    canvas.coords(ball, x - ball_radius, y - ball_radius, x + ball_radius, y + ball_radius)
    canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="white", outline="")
    distance_traveled += math.sqrt(vx**2 + vy**2)

    # --- Burn detection ---
    if clicked_coord and not burn_applied:
        # Convert burn coordinate (real) to canvas pixels
        burn_x_m, burn_y_m = clicked_coord
        burn_x_px = burn_x_m * x_scale
        burn_y_px = burn_y_m * y_scale

        # Calculate distance between ball and burn point (in pixels)
        distance_to_burn = math.sqrt((x - burn_x_px) ** 2 + (y - burn_y_px) ** 2)
        print(f"Distance to burn: {distance_to_burn:.1f}px")

        # Trigger when the ball gets close to the burn marker
        if distance_to_burn < 30:  
            T = thrust_var1.get()
            M_s = mass_var.get()
            burn_duration = 1.0

            # Apply thrust in direction of motion (not planet)
            speed = math.sqrt(vx**2 + vy**2)
            if speed != 0:
                ux = vx / speed
                uy = vy / speed
                ax_burn = T / M_s * ux
                ay_burn = T / M_s * uy
                # --- Add Oberth-like effect: stronger burn when speed is higher ---
                energy_factor = 1 + (speed / 10000)
                vx += ax_burn * burn_duration * energy_factor
                vy += ay_burn * burn_duration * energy_factor

            # Mark as done
            burn_applied = True
            global burn_end_time
            burn_end_time = simulation_time
    

            # Update UI
            burn_time_label.config(text=f"Burn Time: {burn_end_time:.2f} s", fg="#FF0000")
            flash_burn_effect()


            burn_distance_to_planet = math.sqrt((x - planetx)**2 + (y - planety)**2)
            distance_factor = max(0.2, burn_distance_to_planet / (canvas_height / 2))

            # Get all input values for recalculation
            v_i = velocity_var1.get()
            # Use actual current distance from the planet (in meters)
            current_distance_px = math.sqrt((x - planetx)**2 + (y - planety)**2)
            current_distance_m = current_distance_px / x_scale  # convert pixels → meters
            d_m = current_distance_m

            selected_planet = planet_choice.get()
            M = planet_values[selected_planet]["M"]
            r_p = planet_values[selected_planet]["r"]

            # Call your calculation function with burn impact
            _, vf_total, v_inf = calculate_velocity(
                v_i, d_m, M_s, T, True, M, r_p,
                burn_time=burn_duration,
                distance_factor=distance_factor
            )

            if burn_records:
                burn_records[-1]["time"] = burn_end_time
                burn_records[-1]["velocity"] = vf_total

            draw_burn_dots()


            # Update deflection angle
            angle_deg = calculate_deflection_angle(vf_total, d_m, M)

            # Display results
            display_label.config(
                text=f"v_final = {vf_total:.2f} m/s\n"
                     f"v_infinity = {v_inf:.2f} m/s\n"
                     f"Deflection angle = {angle_deg:.2f}°"
            )
            # ---------------------------------------------------------------

    # Continue animation
    if distance_traveled >= curve_trigger_distance:
        prepare_curve()
    else:
        animation_ids.append(root.after(int(time_step * 1000), move_straight))

def prepare_curve():
    global curve_path
    angle_rad = math.radians(turn_angle_deg)
    for i in range(51):
        t = i / 50
        theta = t * angle_rad
        vx_rot = 3 * math.cos(theta)
        curve_y_offset = -0.5
        vy_rot = -3 * math.sin(theta) + curve_y_offset
        curve_path.append((vx_rot, vy_rot))
    move_curve()

def move_curve():
    global x, y, curve_index, animation_id, simulation_time, burn_applied

    if curve_index < len(curve_path):
        # Increment time
        simulation_time += time_step
        time_label.config(text=f"Time: {simulation_time:.2f} s")

        vx, vy = curve_path[curve_index]
        x += vx
        y += vy
        canvas.coords(ball, x - r, y - r, x + r, y + r)
        canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="white", outline="")
        curve_index += 1

        if clicked_coord:
            burn_x_m, burn_y_m = clicked_coord
            burn_x_px = burn_x_m * x_scale
            burn_y_px = burn_y_m * y_scale

            distance_to_burn = math.sqrt((x - burn_x_px)**2 + (y - burn_y_px)**2)
            print(f"[DEBUG] Curve Frame {curve_index:02d} | Dist to burn: {distance_to_burn:.1f}px | Burned: {burn_applied}")

            if not burn_applied and distance_to_burn < 50:
                T = thrust_var1.get()
                M_s = mass_var.get()
                burn_duration = 1.0

                # Apply thrust in direction of velocity
                speed = math.sqrt(vx**2 + vy**2)
                if speed != 0:
                    ux = vx / speed
                    uy = vy / speed
                    ax_burn = T / M_s * ux
                    ay_burn = T / M_s * uy
                    energy_factor = 1 + (speed / 10000)
                    vx += ax_burn * burn_duration * energy_factor
                    vy += ay_burn * burn_duration * energy_factor

                burn_applied = True
                global burn_end_time
                burn_end_time = simulation_time


                burn_time_label.config(text=f"Burn Time: {burn_end_time:.2f} s", fg="#FF0000")
                root.after(1000, lambda: burn_time_label.config(fg="#FF0000"))
                flash_burn_effect()

               


                burn_distance_to_planet = math.sqrt((x - planetx)**2 + (y - planety)**2)
                distance_factor = max(0.2, burn_distance_to_planet / (canvas_height / 2))

                v_i = velocity_var1.get()
                # Use actual current distance from the planet (in meters)
                current_distance_px = math.sqrt((x - planetx)**2 + (y - planety)**2)
                current_distance_m = current_distance_px / x_scale  # convert pixels → meters
                d_m = current_distance_m

                selected_planet = planet_choice.get()
                M = planet_values[selected_planet]["M"]
                r_p = planet_values[selected_planet]["r"]

                # Call your modified velocity calculation function
                _, vf_total, v_inf = calculate_velocity(
                    v_i, d_m, M_s, T, True, M, r_p,
                    burn_time=burn_duration,
                    distance_factor=distance_factor
                )

                if burn_records:
                    burn_records[-1]["time"] = burn_end_time
                    burn_records[-1]["velocity"] = vf_total

                draw_burn_dots()


                angle_deg = calculate_deflection_angle(vf_total, d_m, M)

                # Update display values in the side panel
                display_label.config(
                    text=f"v_final = {vf_total:.2f} m/s\n"
                         f"v_infinity = {v_inf:.2f} m/s\n"
                         f"Deflection angle = {angle_deg:.2f}°"
                )
                # ---------------------------------------------------------------

        # Continue animation
        animation_ids.append(root.after(int(time_step * 1000), move_curve))
    else:
        continue_straight()




def continue_straight():
    angle_rad = math.radians(turn_angle_deg)
    vx = 3 * math.cos(angle_rad)
    curve_y_offset = -0.5
    vy = -3 * math.sin(angle_rad) + curve_y_offset

    def move_out():
        global x, y, animation_id, simulation_time

        # Increment time
        simulation_time += time_step
        time_label.config(text=f"Time: {simulation_time:.2f} s")

        x += vx
        y += vy
        canvas.coords(ball, x - r, y - r, x + r, y + r)
        canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="white", outline="")
        animation_ids.append(root.after(int(time_step * 1000), move_out))

    move_out()



def reset_animation():
    global animation_id, click_used, clicked_coord, click_ball, burn_applied, simulation_time
    global burn_start_time, burn_end_time

    click_used = False
    clicked_coord = None
    burn_applied = False

    # --- Reset timers ---
    simulation_time = 0.0
    burn_start_time = None
    burn_end_time = None

    # --- Update labels ---
    time_label.config(text="Time: 0.00 s")
    burn_time_label.config(text="Burn Time: -- s", fg="white")

    # First, unlock just to ensure Tkinter lets the redraw through
    thrust_slider1.config(state="normal")
    thrust_entry1.config(state="normal")
    
    # Now disable them
    thrust_slider1.config(state="disabled")
    thrust_entry1.config(state="disabled")

    velocity_slider1.config(state="normal")
    velocity_entry1.config(state="normal")
    distance_slider.config(state="normal")
    distance_entry.config(state="normal")
    mass_slider.config(state="normal")
    mass_entry.config(state="normal")

    show_burn_dots_check.config(state=tk.NORMAL)

    # --- Cancel ongoing animations ---
    if click_ball:
        canvas.delete(click_ball)
        click_ball = None
    if animation_id:
        root.after_cancel(animation_id)
        animation_id = None
    for aid in animation_ids:
        root.after_cancel(aid)
    animation_ids.clear()

    # --- Redraw scene ---
    canvas.delete("all")
    draw_diagram(canvas)
    canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2, width=2, fill='#181BDF')

    global planet
    planet = canvas.create_oval(0, 0, 2 * planet_radius, 2 * planet_radius, fill="#181BDF")
    canvas.coords(planet, planetx - planet_radius, planety - planet_radius,
                  planetx + planet_radius, planety + planet_radius)

    d_km = distance_var.get()
    normalized = (d_km - 7000) / (50000 - 7000)
    ball_start_y = canvas_height * (0.60 + normalized * 0.06)

    global x, y, vx, vy, curve_index, curve_path, turn_angle_deg, distance_traveled
    x = 14
    y = ball_start_y + 9
    vx = 0
    vy = 0
    curve_index = 0
    curve_path = []
    turn_angle_deg = 0
    distance_traveled = 0

    # --- Reset the animation ball ---
    global ball
    ball = canvas.create_oval(x, y, x + 2 * ball_radius, y + 2 * ball_radius, fill="white")

    # --- Redraw trajectory lines ---
    example_line = canvas.create_line(
        20, planety + 100,
        planetx - 5, planety + 100,
        width=2, fill="white", dash=(5, 5), tags="trajectory_line"
    )
    points = [
        planetx - 5, planety + 100,
        planetx - 5 + 105, planety + 100 + 5,
        planetx - 5 + 130, planety + 100 - 100
    ]
    canvas.create_line(points, fill="white", width=2, smooth=True, dash=(5, 5), tags="trajectory_line")

    # --- Reset output display ---
    result_label.config(text="")
    display_label.config(text="v_final = \nv_infinity =\nDeflection angle = ")

    run_button.config(state=tk.NORMAL)
    draw_burn_dots()




run_button = tk.Button(side_panel, text="Run Animation", command=run_animation,
                       font=("consolas bold", 12), bg="#D5D8DD", fg="#4D5D72")
run_button.pack(pady=10)

tk.Button(side_panel, text="Reset", command=reset_animation, font=("consolas bold", 12),
          bg="#D5D8DD", fg="#4D5D72").pack(pady=5)

root.mainloop()
