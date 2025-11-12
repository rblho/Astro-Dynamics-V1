import math
G = 6.674e-11  # gravitational constant (m³/kg·s²)

def calculate_velocity(v_i, d_alt, M_s, T, burn_active, M, r, burn_time=160, distance_factor=1.0):

    ## v_i: initial velocity (m/s)
    ## d_alt: altitude above surface (m)
    ## M_s: spacecraft mass (kg)
    ## T: thrust (N)
    ## burn_active: bool
    ## M: planet mass (kg)
    ## r: planet radius (m)


    # Pericenter distance (planet center to spacecraft)
    r_p = r + d_alt

    # Energy conservation for hyperbolic approach
    vf = math.sqrt(v_i**2 + 2 * G * M / r_p)

    # Add thrust effect if burn is active
    if burn_active:
        v_burn = (T / M_s) * burn_time * (1 / distance_factor)
        vf_total = vf + v_burn
        result = f"Final velocity after assist + burn: {vf_total / 1000:.3f} km/s"
    else:
        vf_total = vf
        result = f"Final velocity after gravity assist only: {vf_total / 1000:.3f} km/s"

    # Escape velocity and hyperbolic excess
    v_escape = math.sqrt(2 * G * M / r_p)
    v_inf = math.sqrt(max(0, vf_total**2 - v_escape**2))

    return result, vf_total, v_inf


def calculate_deflection_angle(v_inf, d_alt, M):
    if v_inf <= 0:
        return 0
    delta_rad = 2 * math.atan(G * M / ((d_alt) * v_inf**2))
    return math.degrees(delta_rad)


print(calculate_velocity(1000, 7000000, 1000, 0, False, 5.972e24, 6.371e6))

