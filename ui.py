import tkinter as tk
from calculations import calculate_deflection_angle, calculate_velocity
import math

### CONSTANTS ###
G = 6.67430e-11  # gravitational constant
simulation_time = 0.0  # seconds (starting point 0.0)
time_step = 0.016      # assuming ~60 FPS

### BURN CONSTANTS ###
burn_applied = False
burn_start_time = None
burn_end_time = None 


### PLANET INSERTS (more planets may be added) ###
planet_values = {
    "Earth": {"M": 5.972e24, "r": 6.371e6},
    "Jupiter": {"M": 1.898e27, "r": 6.9911e7},
}

### Scale to change force of gravity so sim looks more realistic ###
planet_gravity_scale = {
    "Earth": 0.1,    # baseline scale (no change)
    "Jupiter": 60.0,  # increase this to make Jupiter's field appear less "tight" when simulation is running (simu only)
}

## SLIDER SETTINGS ###
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

## Disatnce scale (jupiter is farther) ##
planet_visual_scale = {
    "Earth": 1.0,     # baseline
    "Jupiter": 2.0,   # spacecraft sits roughly twice as far visually
}

## Planet colors (will change when I do my own graphics)
planet_colors = {
    "Earth": "#181BDF",   # deep blue
    "Jupiter": "#E58E27"  # orange-brown
}
###########################################################################



### POP UP WINDOW SETTINGS (Do not change, ensures working window on all screens) ###
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

# Diagram for user to select burn point accuratley #
# THIS WILL CHANGE TO UPDATE TRAJECTORY ##
def draw_diagram(canvas):

    canvas.create_line((canvas_width / 2) - 125, canvas_height/2 + 100, (canvas_width / 2) - 125, canvas_height/2, fill="#AA00FF", width=4) # Vertical line
    canvas.create_line((canvas_width / 2) - 55, canvas_height/2 + 85,(canvas_width / 2) - 120, canvas_height/2,fill="#FF007B", width=4)
    vf_ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")
    vf_r = 5
    vf_x = (canvas_width / 2) - 1 
    vf_y = (canvas_height / 2) - 6

    canvas.coords(vf_ball, vf_x - vf_r, vf_y - vf_r, vf_x + vf_r, vf_y + vf_r)
    canvas.tag_raise(vf_ball)

    box_coords = [
        ((canvas_width / 2) - 170, canvas_height/2 + 65, "d"), # Distance
        ((canvas_width / 2) - 120, canvas_height/2 + 45, "θ°"), # Angle
        ((canvas_width / 2) - 32 ,(canvas_height / 2) - 35, "Vf"), # Velocity Final
        ((canvas_width - canvas_width) + 10 ,(canvas_height / 2) + 65, "Vi(r=∞)"), # Velocity initial (coming from infinity)
        ((canvas_width / 2) + 250 , canvas_height/2 - 250, "Vf(r=∞)") # Velocity Final (going into infinity)
    ]

    for x, y, label in box_coords:
        canvas.create_text(x + 30, y + 15, text=label, font=("consolas bold", 12), fill="White", anchor="center") 

# Conversion to real world coords #
def to_real_coords(x_px, y_px):
    x_m = x_px / x_scale
    y_m = y_px / y_scale
    return x_m, y_m

# Burn behind the spacecraft during burn point
def flash_burn_effect(thrust_active=True):
    """Flash red if thrust applied; stay unchanged if no thrust."""
    try:
        if not thrust_active:
            return  # skip flashing entirely
        canvas.itemconfig(ball, fill="red")
        root.after(1000, lambda: canvas.itemconfig(ball, fill="white"))
    except:
        pass

# Hover over feature (basically useless)
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

## Update sliders based on which planet is chose ##
def update_sliders_for_planet(*args):
    planet = planet_choice.get()
    settings = planet_slider_settings.get(planet, planet_slider_settings["Earth"])

    # Velocity slider
    velocity_slider1.config(from_=settings["v_max"], to=settings["v_min"])
    velocity_var1.set(settings["v_min"])

    # Thrust slider
    thrust_slider1.config(from_=settings["t_max"], to=settings["t_min"])
    thrust_var1.set(settings["t_min"])

    # Mass slider
    mass_slider.config(from_=settings["m_max"], to=settings["m_min"])
    mass_var.set(settings["m_min"])

    # Distance slider (don’t force reset — keep current)
    distance_slider.config(from_=settings["d_max"], to=settings["d_min"])

    # Only adjust spacecraft if user manually moves the slider,
    # not when planet changes or program starts.
    current_val = distance_var.get()
    if not (settings["d_min"] <= current_val <= settings["d_max"]):
        # Clamp if out of range for the new planet
        distance_var.set(settings["d_min"])
        current_val = settings["d_min"]

    update_spacecraft_position(current_val)
    update_planet_colors()

# When planet is chosen #
def update_planet_colors(*args):
    color = planet_colors[planet_choice.get()]
    # recolor planet
    for pid in canvas.find_withtag("planet"):
        canvas.itemconfig(pid, fill=color)
    # recolor horizontal line
    for lid in canvas.find_withtag("planet_line"):
        canvas.itemconfig(lid, fill=color)


## FRAMING ##
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

side_panel = tk.Frame(main_frame, width=280, bg='#4D5D72')
side_panel.pack(side=tk.RIGHT, fill=tk.Y)
side_panel.pack_propagate(False)

canvas = tk.Canvas(main_frame, width=canvas_width, height=canvas_height, bg="black")
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

planet_choice = tk.StringVar(value="Earth")
planet_menu = tk.OptionMenu(canvas, planet_choice, *planet_values.keys())
planet_menu.config(font=("consolas", 10), bg="#D5D8DD", fg="#4D5D72", highlightthickness=0)
planet_menu.place(x=20, y=20)

planet_choice.trace_add("write", update_sliders_for_planet)
planet_choice.trace_add("write", update_planet_colors)

planetx = canvas_width / 2 - 125
planety = canvas_height / 2
ball_radius = 4
planet_radius = 60


####################### BURN DOTS ##############################

### BURN point selection ###
burn_menu_button = tk.Menubutton(canvas, text="Show Burns ▼",
                                 font=("consolas", 9),
                                 bg="#D5D8DD", fg="#4D5D72",
                                 relief="raised", direction="below", width=14, height=1)
burn_menu_button.place(x=120, y=20)

burn_menu = tk.Menu(burn_menu_button, tearoff=0, bg="#D5D8DD", fg="#4D5D72")
burn_menu_button.config(menu=burn_menu)

selected_burns = {} # Selected burns list storage
burn_records = [] # Burn records storage
burn_markers = [] # Burn dots

show_burn_dots_var = tk.BooleanVar(value=False) # False first

## Drawing burn dots in all situations ##
def draw_burn_dots():
    burn_dot_radius = 5
    canvas.delete("burn_dot")

    if show_burn_dots_var.get():
        for i, record in enumerate(burn_records):
            x_m, y_m = record["coords"]
            x_px = x_m * x_scale
            y_px = y_m * y_scale

            # Determine dot color based on burn type
            if record["time"] is None:
                dot_color = "#BC0101"  # pending burn (darker red)
            elif record.get("thrust", 0) == 0:
                dot_color = "#FFA500"  # orange = 0-thrust burn
            else:
                dot_color = "#FF0000"  # red = normal burn

            # Draw the dot  
            dot = canvas.create_oval(
                x_px - burn_dot_radius, y_px - burn_dot_radius,
                x_px + burn_dot_radius, y_px + burn_dot_radius,
                fill=dot_color, outline="", tags=("burn_dot", f"dot_{i}")
            )

            # Tooltip text
            if record["time"] is not None:
                tt_text = (f"Burn time: {record['time']:.2f} s\n"
                    f"v∞: {record['velocity']:.2f} m/s")
            else:
                tt_text = "Pending burn"

            tooltip = ToolTip(canvas, text=tt_text)

            def on_enter(event, tt=tooltip):
                tt.showtip(event.x_root, event.y_root)
            def on_leave(event, tt=tooltip):
                tt.hidetip()

            canvas.tag_bind(f"dot_{i}", "<Enter>", on_enter)
            canvas.tag_bind(f"dot_{i}", "<Leave>", on_leave)


def update_burn_dropdown():
    burn_menu.delete(0, "end")
    selected_burns.clear()

    if not burn_records:
        burn_menu.add_command(label="No burns yet")
        return

    for i, record in enumerate(burn_records, 1):
        burn_label = (f"Burn #{i} | "
              f"{'t=' + str(round(record['time'],2)) + 's' if record['time'] else 'Pending'} | "
              f"{'v∞=' + str(round(record['velocity'],2)) + ' m/s' if record['velocity'] else ''}")


        var = tk.BooleanVar(value=False)
        selected_burns[i] = var

        def toggle_burn(i=i, var=var):
            if var.get():
                show_burn_highlight(i)
            else:
                hide_burn_highlight(i)

        # Main burn checkbox
        burn_menu.add_checkbutton(label=burn_label, variable=var, command=toggle_burn)

        # Add a delete icon aligned to the right of the label
        burn_menu.add_command(
            label=f" Delete Burn #{i}",
            command=lambda idx=i: delete_burn_record(idx)
        )

    burn_menu.add_separator()
    burn_menu.add_command(label="Clear All Burns", command=clear_burn_dots)

def delete_burn_record(index):
    global clicked_coord, click_used, click_ball, burn_applied

    if 0 < index <= len(burn_records):

        burn_records.pop(index - 1)

        tag = f"highlight_{index}"
        canvas.delete(tag)

        dot_tag = f"dot_{index - 1}"  
        canvas.delete(dot_tag)

       ## Burn dots reindex to stay in order #
        for i in range(len(burn_records)):
            old_dot_tag = f"dot_{i+1}"
            new_dot_tag = f"dot_{i}"
            if canvas.find_withtag(old_dot_tag):
                canvas.addtag_withtag(new_dot_tag, old_dot_tag)
                canvas.dtag(old_dot_tag)

            old_high_tag = f"highlight_{i+2}"
            new_high_tag = f"highlight_{i+1}"
            if canvas.find_withtag(old_high_tag):
                canvas.addtag_withtag(new_high_tag, old_high_tag)
                canvas.dtag(old_high_tag)

        clicked_coord = None
        click_used = False
        burn_applied = False

        if click_ball:
            canvas.delete(click_ball)
            click_ball = None

        draw_burn_dots()
        update_burn_dropdown()


def show_burn_highlight(index):
    if 0 < index <= len(burn_records):
        record = burn_records[index - 1]
        x_m, y_m = record["coords"]
        x_px = x_m * x_scale
        y_px = y_m * y_scale

        tag = f"highlight_{index}"
        canvas.delete(tag)

        if record.get("time") is None:
            highlight_color = "#FF0084"   # pink = pending
        elif record.get("thrust", 0) == 0:
            highlight_color = "#FFD700"   # yellow = 0 thrust
        else:
            highlight_color = "#FF0000"   # red = normal

        canvas.create_oval(
            x_px - ball_radius * 1.6, y_px - ball_radius * 1.6,
            x_px + ball_radius * 1.6, y_px + ball_radius * 1.6,
            outline=highlight_color, width=2, tags=tag
        )


# Remove burn highlight for given burn #
def hide_burn_highlight(index):
    tag = f"highlight_{index}"
    canvas.delete(tag)

# Reseting burn records #
def clear_burn_dots():
    canvas.delete("burn_dot")
    burn_records.clear()

    if "burn_markers" in globals():
        burn_markers.clear()
    update_burn_dropdown()


## Sets initial slider values when program opens #
velocity_var1 = tk.IntVar(value=1000)
thrust_var1 = tk.IntVar(value=0)
mass_var = tk.IntVar(value=1000)
distance_var = tk.DoubleVar(value=7000)

draw_diagram(canvas) # Draw diagram on canvas for selections

## ball radius / spacecraft / Planet (all control, mainly creating and managing radius) ##
global ball
animation_id = None
animation_ids = []

ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")
initial_d_km = distance_var.get()
normalized = (initial_d_km - 7000) / (50000 - 7000)
ball_start_y = canvas_height * (0.595 + normalized * 0.06)
x = 14
y = ball_start_y + 80
canvas.coords(ball, x, y, x + 2 * ball_radius, y + 2 * ball_radius)

planet = canvas.create_oval(0, 0, 2 * planet_radius, 2 * planet_radius, fill="#181BDF", tags='planet')
canvas.coords(planet, planetx - planet_radius, planety - planet_radius,
              planetx + planet_radius, planety + planet_radius)
canvas.create_line(0, canvas_height / 2, canvas_width, canvas_height / 2, width=2, fill='#181BDF', tags="planet_line")

label = tk.Label(side_panel, text="Controls", fg="#4D5D72", bg="#D5D8DD", font=("consolas bold", 14))
label.pack(pady=10)

slider_frame = tk.Frame(side_panel, bg='#4D5D72')
slider_frame.pack(pady=5)
slider_frame.grid_columnconfigure(1, minsize=30)

# Update vals #
def update_velocity1(val): velocity_var1.set(int(float(val))) 
def update_thrust1(val): thrust_var1.set(int(float(val)))
def update_mass(val): mass_var.set(int(float(val)))

## Changing trajectory based on entered values ##
def update_spacecraft_position(val):
    d_km = float(val)
    planet = planet_choice.get()
    settings = planet_slider_settings.get(planet, planet_slider_settings["Earth"])

    planet = planet_choice.get()
    settings = planet_slider_settings.get(planet, planet_slider_settings["Earth"])
    scale_factor = planet_visual_scale.get(planet, 1.0)

    normalized = (d_km - settings["d_min"]) / (settings["d_max"] - settings["d_min"])
    ball_start_y = canvas_height * (0.595 + normalized * 0.06 * scale_factor)

    x = 15
    y = ball_start_y + 25
    canvas.coords(ball, x, y, x + 2 * ball_radius, y + 2 * ball_radius)

    ball_coords = canvas.coords(ball)
    ball_center_y = (ball_coords[1] + ball_coords[3]) / 2

    canvas.coords("trajectory_line",
                  20, ball_center_y,
                  planetx - 5, ball_center_y)

    for curve_id in canvas.find_withtag("curve_line"):
        curve_coords = canvas.coords(curve_id)
        if len(curve_coords) < 6:
            continue 

        x_end_fixed = curve_coords[-2]
        y_end_fixed = curve_coords[-1]


        new_start_x = planetx - 5
        new_start_y = ball_center_y

     
        control_x = new_start_x + 105
        control_y = new_start_y + 5

        canvas.coords(curve_id,
                      new_start_x, new_start_y,
                      control_x, control_y,
                      x_end_fixed, y_end_fixed)


    distance_var.set(d_km)


## When the line is clicked ##
def on_line_click(event):
    global click_used, clicked_coord, click_ball
    pending_ball_radius = 5

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
            update_burn_dropdown() 


            if click_ball:
                canvas.delete(click_ball)
            click_ball = canvas.create_oval(
                event.x - pending_ball_radius, event.y - pending_ball_radius,
                event.x + pending_ball_radius, event.y + pending_ball_radius,
                fill="#BC0101" #darker
            )

            click_used = True
            draw_burn_dots()


## Example trajectory line ##
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
curve_line = canvas.create_line(points, fill="white", width=2, smooth=True,
                                dash=(5, 5), tags=("trajectory_line", "curve_line"))

canvas.tag_bind(curve_line, "<Button-1>", on_line_click)

# Click on canvas #
click_used = False
clicked_coord = None
click_ball = None 

canvas.tag_bind("trajectory_line", "<Button-1>", on_line_click)
canvas.tag_bind("curve_line", "<Button-1>", on_line_click)


## Sliders and Entry Boxes ##
tk.Label(slider_frame, text="Velocity (m/s)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=0, column=0, pady=(0, 5))
velocity_slider1 = tk.Scale(slider_frame, from_=50000, to=1000, orient=tk.VERTICAL, length=120,
                            fg="white", bg="#4D5D72", troughcolor="#4D5D72",
                            highlightthickness=0, command=update_velocity1)
velocity_slider1.grid(row=1, column=0)
velocity_entry1 = tk.Entry(slider_frame, textvariable=velocity_var1, width=10, justify='center')
velocity_entry1.grid(row=2, column=0, pady=(5, 10))
velocity_var1.trace_add("write", lambda *args: velocity_slider1.set(velocity_var1.get()))

tk.Label(slider_frame, text="Thrust (N)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=0, column=2, pady=(0, 5))
thrust_slider1= tk.Scale(slider_frame, from_=10000, to=0, orient=tk.VERTICAL, length=120,
                          fg="white", bg="#4D5D72", troughcolor="#4D5D72",
                          highlightthickness=0, command=update_thrust1)
thrust_slider1.grid(row=1, column=2)
thrust_entry1 = tk.Entry(slider_frame, textvariable=thrust_var1, width=10, justify='center')
thrust_entry1.grid(row=2, column=2, pady=(5, 10))
thrust_var1.trace_add("write", lambda *args: thrust_slider1.set(thrust_var1.get()))

thrust_slider1.config(state="disabled")
thrust_entry1.config(state="disabled")

tk.Label(slider_frame, text="Spacecraft Mass (kg)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=3, column=0, pady=(0, 5))
mass_slider = tk.Scale(slider_frame, from_=100000, to=1000, orient=tk.VERTICAL, length=120,
                       fg="white", bg="#4D5D72", troughcolor="#4D5D72",
                       highlightthickness=0, command=update_mass)
mass_slider.grid(row=4, column=0)
mass_entry = tk.Entry(slider_frame, textvariable=mass_var, width=10, justify='center')
mass_entry.grid(row=5, column=0, pady=(5, 10))
mass_var.trace_add("write", lambda *args: mass_slider.set(mass_var.get()))

tk.Label(slider_frame, text="Distance (km)", fg="white", bg="#4D5D72", font=('consolas bold', 10)).grid(row=3, column=2, pady=(0, 5))
earth_settings = planet_slider_settings["Earth"]
distance_slider = tk.Scale(
    slider_frame,
    from_=earth_settings["d_max"],
    to=earth_settings["d_min"],
    resolution=10,
    orient=tk.VERTICAL,
    length=120,
    fg="white",
    bg="#4D5D72",
    troughcolor="#4D5D72",
    highlightthickness=0,
    command=update_spacecraft_position
)
distance_slider.grid(row=4, column=2)
distance_entry = tk.Entry(slider_frame, textvariable=distance_var, width=10, justify='center')
distance_entry.grid(row=5, column=2, pady=(5, 10))
distance_var.trace_add("write", lambda *args: distance_slider.set(distance_var.get()))

update_sliders_for_planet()

## SPACER IN CONTROL PANEL ##
tk.Label(slider_frame, text="", bg="#4D5D72").grid(row=6, column=0, columnspan=3, pady=5)

## Simulation Timers (will change) ##
timer_frame = tk.Frame(slider_frame, bg="#4D5D72")
timer_frame.grid(row=8, column=0, columnspan=3, pady=(4, 4))

time_label = tk.Label(timer_frame, text="Time: 0.00 s",
                      font=("consolas", 10), fg="white", bg="#3B4148")
time_label.pack(side="left", padx=(0, 10))

burn_time_label = tk.Label(timer_frame, text="Burn Time: -- s",
                           font=("consolas", 10), fg="white", bg="#3B4148")
burn_time_label.pack(side="left")

# Show burn dots #
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
show_burn_dots_check.pack(pady=(0, 1), anchor="center")  

result_label = tk.Label(
    side_panel,
    text="",
    fg="white",
    bg="#4D5D72",
    font=("consolas", 9)   
)
result_label.pack(pady=(1, 0), anchor="center")

display_frame = tk.Frame(side_panel, bg="#D5D8DD", bd=3, relief=tk.SUNKEN)
display_frame.pack(pady=(2, 4), padx=8, fill=tk.X)

display_label = tk.Label(
    display_frame,
    text="v_final = \nv_infinity = \nDeflection angle = ",
    justify="left",
    anchor="w",
    bg="#D5D8DD",
    fg="#4D5D72",
    font=("consolas", 9)  
)
display_label.pack(padx=6, pady=4, anchor="w")


### RUNS ANIMATION ###
def run_animation():
    global x, y, r, pr, vx, vy, curve_index, curve_path, turn_angle_deg, distance_traveled, ball, planet
    run_button.config(state=tk.DISABLED)
    show_burn_dots_check.config(state=tk.DISABLED)
    planet_menu.config(state="disabled")
    show_burn_dots_var.set(False)
    draw_burn_dots()  

    canvas.delete("example_line")
    canvas.delete("all")

    color = planet_colors[planet_choice.get()]

    canvas.create_line(
        0, canvas_height / 2,
        canvas_width, canvas_height / 2,
        width=2, fill=color, tags="planet_line"
    )

    planet = canvas.create_oval(
        0, 0, 2 * planet_radius, 2 * planet_radius,
        fill=color, tags="planet"
    )

    ball = canvas.create_oval(0, 0, 2 * ball_radius, 2 * ball_radius, fill="white")
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
    planet = planet_choice.get()
    settings = planet_slider_settings.get(planet, planet_slider_settings["Earth"])
    normalized = (d_km - settings["d_min"]) / (settings["d_max"] - settings["d_min"])
    ball_start_y = canvas_height * (0.595 + normalized * 0.06)
    x = 2
    y = ball_start_y + 25
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
        curve_trigger_distance = 480 + (turn_angle_deg - 100) * 2
    else:
        curve_trigger_distance = 480
    distance_traveled = 0
    canvas.coords(ball, x, y, x + 2 * ball_radius, y + 2 * ball_radius)
    move_straight()


time_step = 0.016  
simulation_time = 0.0

## If craft touched the edge of the screen the simulation ends ##
def check_boundary_collision():
    global animation_ids

    if (x - ball_radius <= 0 or
        x + ball_radius >= canvas_width - 275 or
        y - ball_radius <= 0 or
        y + ball_radius >= canvas_height):

        # Cancel all scheduled motion frames
        for aid in animation_ids:
            root.after_cancel(aid)
        animation_ids.clear()

        run_button.config(state=tk.DISABLED)
        burn_time_label.config(fg="#FF5555")

        return True
    return False


## moves the craft straight with slight application of force of gravity ##
def move_straight():
    global x, y, vx, vy, distance_traveled, burn_applied, simulation_time, ball_radius

    planet_name = planet_choice.get()
    M_p = planet_values[planet_name]["M"]

    # Increment time #
    simulation_time += time_step
    time_label.config(text=f"Time: {simulation_time:.2f} s")

    # Gravitational acceleration 
    dx = planetx - x
    dy = planety - y
    r_squared = dx**2 + dy**2
    r = math.sqrt(r_squared)
    if r_squared > 0:
        scale_factor = planet_gravity_scale.get(planet_name, 1.0)
        F = (G * M_p / r_squared) / (1e13 * 2 * scale_factor)
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

    # Burn Detection #
    if clicked_coord and not burn_applied:
        # Convert burn coordinate (real) to canvas pixels
        burn_x_m, burn_y_m = clicked_coord
        burn_x_px = burn_x_m * x_scale
        burn_y_px = burn_y_m * y_scale

        # Calculate distance between spacecraft and burn point
        distance_to_burn_px = math.sqrt((x - burn_x_px) ** 2 + (y - burn_y_px) ** 2)
        distance_to_burn_m = distance_to_burn_px * (real_width_m / canvas_width)
        threshold_m = 5_000_000  # ~5,000 km tolerance for triggering burn

        print(f"Distance to burn: {distance_to_burn_m/1000:.1f} km")

        if distance_to_burn_m < threshold_m:
            T = thrust_var1.get()
            M_s = mass_var.get()
            burn_duration = 1.0
            burn_applied = True
            global burn_end_time
            burn_end_time = simulation_time

            ## If no thrust is detected ##
            if T <= 0:
                v_i = velocity_var1.get()
                selected_planet = planet_choice.get()
                M = planet_values[selected_planet]["M"]
                r_p = planet_values[selected_planet]["r"]

                current_distance_px = math.sqrt((x - planetx)**2 + (y - planety)**2)
                current_distance_m = current_distance_px * (real_width_m / canvas_width)
                d_m = current_distance_m

                _, vf_total, v_inf = calculate_velocity(
                    v_i, d_m, M_s, 0, True, M, r_p,
                    burn_time=0, distance_factor=1.0
                )

                if burn_records:
                    burn_records[-1]["time"] = burn_end_time
                    burn_records[-1]["velocity"] = v_inf
                    burn_records[-1]["thrust"] = T


                update_burn_dropdown()
                draw_burn_dots()

                burn_time_label.config(text=f"Burn Time: {burn_end_time:.2f} s", fg="#FFA500")
                

                angle_deg = calculate_deflection_angle(vf_total, d_m, M)
                display_label.config(
                    text=f"v_final = {vf_total:.2f} m/s\n"
                         f"v_infinity = {v_inf:.2f} m/s\n"
                         f"Deflection angle = {angle_deg:.2f}°"
                )

                animation_ids.append(root.after(int(time_step * 1000), move_straight))
                return

            else:
                speed = math.sqrt(vx**2 + vy**2)
                if speed != 0:
                    ux = vx / speed
                    uy = vy / speed
                    ax_burn = T / M_s * ux
                    ay_burn = T / M_s * uy
                    vx += ax_burn * burn_duration / 5
                    vy += ay_burn * burn_duration / 5

                burn_time_label.config(text=f"Burn Time: {burn_end_time:.2f} s", fg="#FF0000")
                flash_burn_effect()

                burn_distance_to_planet = math.sqrt((x - planetx)**2 + (y - planety)**2)
                distance_factor = max(0.2, burn_distance_to_planet / (canvas_height / 2))

                v_i = velocity_var1.get()
                current_distance_px = math.sqrt((x - planetx)**2 + (y - planety)**2)
                current_distance_m = current_distance_px * (real_width_m / canvas_width)
                d_m = current_distance_m

                selected_planet = planet_choice.get()
                M = planet_values[selected_planet]["M"]
                r_p = planet_values[selected_planet]["r"]

                _, vf_total, v_inf = calculate_velocity(
                    v_i, d_m, M_s, T, True, M, r_p,
                    burn_time=burn_duration, distance_factor=distance_factor
                )

                if burn_records:
                    burn_records[-1]["time"] = burn_end_time
                    burn_records[-1]["velocity"] = v_inf
                    burn_records[-1]["thrust"] = T


                update_burn_dropdown()
                draw_burn_dots()

                angle_deg = calculate_deflection_angle(vf_total, d_m, M)
                display_label.config(
                    text=f"v_final = {vf_total:.2f} m/s\n"
                         f"v_infinity = {v_inf:.2f} m/s\n"
                         f"Deflection angle = {angle_deg:.2f}°"
                )

    if check_boundary_collision():
        return

    # Continue animation
    if distance_traveled >= curve_trigger_distance:
        prepare_curve()
    else:
        animation_ids.append(root.after(int(time_step * 1000), move_straight))


## Curve logic ##############################
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

    planet_name = planet_choice.get()
    M_p = planet_values[planet_name]["M"]

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

            distance_to_burn_px = math.sqrt((x - burn_x_px)**2 + (y - burn_y_px)**2)
            distance_to_burn_m = distance_to_burn_px * (real_width_m / canvas_width)
            threshold_m = 5_000_000  # ~5,000 km threshold for burn detection

            print(f"[DEBUG] Curve Frame {curve_index:02d} | Dist to burn: {distance_to_burn_m/1000:.1f} km | Burned: {burn_applied}")

            if not burn_applied and distance_to_burn_m < threshold_m:
                T = thrust_var1.get()
                M_s = mass_var.get()
                burn_duration = 1.0
                burn_applied = True
                global burn_end_time
                burn_end_time = simulation_time


                if T <= 0:
                    v_i = velocity_var1.get()
                    selected_planet = planet_choice.get()
                    M = planet_values[selected_planet]["M"]
                    r_p = planet_values[selected_planet]["r"]

                    current_distance_px = math.sqrt((x - planetx)**2 + (y - planety)**2)
                    current_distance_m = current_distance_px * (real_width_m / canvas_width)
                    d_m = current_distance_m

                    _, vf_total, v_inf = calculate_velocity(
                        v_i, d_m, M_s, 0, True, M, r_p,
                        burn_time=0, distance_factor=1.0
                    )

                    if burn_records:
                        burn_records[-1]["time"] = burn_end_time
                        burn_records[-1]["velocity"] = v_inf
                        burn_records[-1]["thrust"] = T


                    update_burn_dropdown()
                    draw_burn_dots()

                    burn_time_label.config(text=f"Burn Time: {burn_end_time:.2f} s", fg="#FFA500")

                    angle_deg = calculate_deflection_angle(vf_total, d_m, M)
                    display_label.config(
                        text=f"v_final = {vf_total:.2f} m/s\n"
                             f"v_infinity = {v_inf:.2f} m/s\n"
                             f"Deflection angle = {angle_deg:.2f}°"
                    )

                    animation_ids.append(root.after(int(time_step * 1000), move_curve))
                    return


                else:
                    speed = math.sqrt(vx**2 + vy**2)
                    if speed != 0:
                        ux = vx / speed
                        uy = vy / speed
                        ax_burn = T / M_s * ux
                        ay_burn = T / M_s * uy
                        vx += ax_burn * burn_duration
                        vy += ay_burn * burn_duration

                    burn_time_label.config(text=f"Burn Time: {burn_end_time:.2f} s", fg="#FF0000")
                    flash_burn_effect()

                    burn_distance_to_planet = math.sqrt((x - planetx)**2 + (y - planety)**2)
                    distance_factor = max(0.2, burn_distance_to_planet / (canvas_height / 2))

                    v_i = velocity_var1.get()
                    current_distance_px = math.sqrt((x - planetx)**2 + (y - planety)**2)
                    current_distance_m = current_distance_px * (real_width_m / canvas_width)
                    d_m = current_distance_m

                    selected_planet = planet_choice.get()
                    M = planet_values[selected_planet]["M"]
                    r_p = planet_values[selected_planet]["r"]

                    _, vf_total, v_inf = calculate_velocity(
                        v_i, d_m, M_s, T, True, M, r_p,
                        burn_time=burn_duration, distance_factor=distance_factor
                    )

                    if burn_records:
                        burn_records[-1]["time"] = burn_end_time
                        burn_records[-1]["velocity"] = v_inf
                        burn_records[-1]["thrust"] = T


                    update_burn_dropdown()
                    draw_burn_dots()

                    angle_deg = calculate_deflection_angle(vf_total, d_m, M)
                    display_label.config(
                        text=f"v_final = {vf_total:.2f} m/s\n"
                             f"v_infinity = {v_inf:.2f} m/s\n"
                             f"Deflection angle = {angle_deg:.2f}°"
                    )

        if check_boundary_collision():
            return

        animation_ids.append(root.after(int(time_step * 1000), move_curve))
    else:
        continue_straight()
################################################################################


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

        if check_boundary_collision():
            return

        animation_ids.append(root.after(int(time_step * 1000), move_out))

    move_out()


## Reset ###
def reset_animation():
    global animation_id, click_used, clicked_coord, click_ball, burn_applied, simulation_time, planet
    global burn_start_time, burn_end_time

    click_used = False
    clicked_coord = None
    burn_applied = False

    
    simulation_time = 0.0
    burn_start_time = None
    burn_end_time = None

    # Update Labels #
    time_label.config(text="Time: 0.00 s")
    burn_time_label.config(text="Burn Time: -- s", fg="white")

    # First unlock and then disable thrust controls
    thrust_slider1.config(state="normal")
    thrust_entry1.config(state="normal")
    thrust_slider1.config(state="disabled")
    thrust_entry1.config(state="disabled")

    # Re enable sliders for new setup
    velocity_slider1.config(state="normal")
    velocity_entry1.config(state="normal")
    distance_slider.config(state="normal")
    distance_entry.config(state="normal")
    mass_slider.config(state="normal")
    mass_entry.config(state="normal")

    show_burn_dots_check.config(state=tk.NORMAL)
    planet_menu.config(state="normal")


    # Cancel all ongoing animations #
    if click_ball:
        canvas.delete(click_ball)
        click_ball = None
    if animation_id:
        root.after_cancel(animation_id)
        animation_id = None
    for aid in animation_ids:
        root.after_cancel(aid)
    animation_ids.clear()

    # Redraw scene #
    canvas.delete("all")
    draw_diagram(canvas)

    color = planet_colors[planet_choice.get()]

    canvas.create_line(
        0, canvas_height / 2,
        canvas_width, canvas_height / 2,
        width=2, fill=color, tags="planet_line"
    )
    
    planet = canvas.create_oval(
        0, 0, 2 * planet_radius, 2 * planet_radius,
        fill=color, tags="planet"
    )
    update_planet_colors()

    canvas.coords(planet, planetx - planet_radius, planety - planet_radius,
                  planetx + planet_radius, planety + planet_radius)

    # Reset animation ball #
    d_km = distance_var.get()
    planet = planet_choice.get()
    settings = planet_slider_settings.get(planet, planet_slider_settings["Earth"])
    planet = planet_choice.get()
    settings = planet_slider_settings.get(planet, planet_slider_settings["Earth"])
    scale_factor = planet_visual_scale.get(planet, 1.0)

    normalized = (d_km - settings["d_min"]) / (settings["d_max"] - settings["d_min"])

    # push the spacecraft farther vertically based on planet type
    ball_start_y = canvas_height * (0.595 + normalized * 0.06 * scale_factor)

    global x, y, vx, vy, curve_index, curve_path, turn_angle_deg, distance_traveled
    x = 14
    y = ball_start_y + 25
    vx = vy = 0
    curve_index = 0
    curve_path = []
    turn_angle_deg = 0
    distance_traveled = 0

    global ball
    ball = canvas.create_oval(x, y, x + 2 * ball_radius, y + 2 * ball_radius, fill="white")

    # Redraw trajectory line #
    example_line = canvas.create_line(
        20, planety + 100,
        planetx - 5, planety + 100,
        width=2, fill="white", dash=(5, 5), tags="trajectory_line"
    )

    # --- Redraw curve (tagged properly) ---
    points = [
        planetx - 5, planety + 100,
        planetx - 5 + 105, planety + 100 + 5,
        planetx - 5 + 130, planety + 100 - 100
    ]
    curve_line = canvas.create_line(points, fill="white", width=2, smooth=True,
                                    dash=(5, 5), tags=("trajectory_line", "curve_line"))


    canvas.tag_bind(curve_line, "<Button-1>", on_line_click)

    result_label.config(text="")
    display_label.config(text="v_final = \nv_infinity =\nDeflection angle = ")

    run_button.config(state=tk.NORMAL)
    draw_burn_dots()

    update_spacecraft_position(distance_var.get())


run_button = tk.Button(side_panel, text="Run Animation", command=run_animation,
                       font=("consolas bold", 12), bg="#D5D8DD", fg="#4D5D72")
run_button.pack(pady=10)

tk.Button(side_panel, text="Reset", command=reset_animation, font=("consolas bold", 12),
          bg="#D5D8DD", fg="#4D5D72").pack(pady=(10,10))

root.mainloop()
