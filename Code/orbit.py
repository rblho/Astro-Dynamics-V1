        
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import math
from datetime import datetime
import os

class OrbitalSimulator:
    def __init__(self):
        # Physical constants (scaled for simulation)
        self.G = 6.67430e-11  # Gravitational constant
        self.AU = 1.496e11    # Astronomical unit in meters
        self.EARTH_MASS = 5.972e24
        self.SUN_MASS = 1.989e30
        self.MARS_MASS = 6.39e23
        self.JUPITER_MASS = 1.898e27
        
        # Simulation parameters
        self.dt = 3600 * 24  # Time step: 1 day in seconds
        self.scale = 1e-11   # Scaling factor for display
        
        # Initialize celestial bodies
        self.sun = {'mass': self.SUN_MASS, 'pos': np.array([0.0, 0.0]), 'vel': np.array([0.0, 0.0])}
        self.earth = {'mass': self.EARTH_MASS, 'pos': np.array([self.AU, 0.0]), 'vel': np.array([0.0, 29780.0])}
        self.mars = {'mass': self.MARS_MASS, 'pos': np.array([1.52 * self.AU, 0.0]), 'vel': np.array([0.0, 24077.0])}
        self.jupiter = {'mass': self.JUPITER_MASS, 'pos': np.array([5.2 * self.AU, 0.0]), 'vel': np.array([0.0, 13070.0])}
        
        # Spacecraft initial conditions
        self.spacecraft = {
            'mass': 1000.0,  # 1000 kg spacecraft
            'pos': np.array([self.AU + 400000.0, 0.0]),  # 400 km above Earth
            'vel': np.array([0.0, 30780.0])  # Slightly faster than Earth
        }
        
        # Storage for trajectories
        self.trajectories = {
            'sun': [self.sun['pos'].copy()],
            'earth': [self.earth['pos'].copy()],
            'mars': [self.mars['pos'].copy()],
            'jupiter': [self.jupiter['pos'].copy()],
            'spacecraft': [self.spacecraft['pos'].copy()]
        }
        
        # Data storage for analysis
        self.data_log = {
            'time': [],
            'spacecraft_pos': [],
            'spacecraft_vel': [],
            'orbital_energy': [],
            'distance_sun': [],
            'distance_earth': [],
            'distance_mars': [],
            'distance_jupiter': [],
            'velocity_magnitude': [],
            'orbital_elements': [],
            'burn_events': []
        }
        
        # Burn parameters
        self.burn_active = False
        self.burn_direction = 0.0  # Angle in radians
        self.burn_magnitude = 0.0  # m/s
        
    def gravitational_force(self, m1, pos1, m2, pos2):
        """Calculate gravitational force between two bodies"""
        r_vec = pos2 - pos1
        r_mag = np.linalg.norm(r_vec)
        if r_mag == 0:
            return np.array([0.0, 0.0])
        
        force_mag = self.G * m1 * m2 / (r_mag ** 2)
        force_vec = force_mag * r_vec / r_mag
        return force_vec
    
    def calculate_total_force(self, body, other_bodies):
        """Calculate total gravitational force on a body"""
        total_force = np.array([0.0, 0.0])
        for other in other_bodies:
            if other != body:
                force = self.gravitational_force(body['mass'], body['pos'], other['mass'], other['pos'])
                total_force += force
        return total_force
    
    def apply_burn(self, time_days=None):
        """Apply propulsive burn to spacecraft"""
        if self.burn_active and self.burn_magnitude > 0:
            burn_vec = np.array([
                np.cos(self.burn_direction) * self.burn_magnitude,
                np.sin(self.burn_direction) * self.burn_magnitude
            ])
            self.spacecraft['vel'] += burn_vec
            
            # Log burn event
            burn_event = {
                'time': time_days if time_days else len(self.data_log['time']),
                'magnitude': self.burn_magnitude,
                'direction_deg': np.degrees(self.burn_direction),
                'position': self.spacecraft['pos'].copy(),
                'velocity_before': self.spacecraft['vel'] - burn_vec,
                'velocity_after': self.spacecraft['vel'].copy()
            }
            self.data_log['burn_events'].append(burn_event)
            
            self.burn_active = False  # Single impulse burn
    
    def update_bodies(self):
        """Update positions and velocities using Verlet integration"""
        bodies = [self.sun, self.earth, self.mars, self.jupiter, self.spacecraft]
        
        # Calculate current time
        current_time = len(self.data_log['time']) * self.dt / (24 * 3600)
        
        # Calculate forces
        forces = {}
        for body in bodies:
            forces[id(body)] = self.calculate_total_force(body, bodies)
        
        # Apply burns to spacecraft
        self.apply_burn(current_time)
        
        # Update velocities and positions
        for body in bodies:
            if body != self.sun:  # Keep sun stationary
                acceleration = forces[id(body)] / body['mass']
                body['vel'] += acceleration * self.dt
                body['pos'] += body['vel'] * self.dt
        
        # Store trajectories
        self.trajectories['sun'].append(self.sun['pos'].copy())
        self.trajectories['earth'].append(self.earth['pos'].copy())
        self.trajectories['mars'].append(self.mars['pos'].copy())
        self.trajectories['jupiter'].append(self.jupiter['pos'].copy())
        self.trajectories['spacecraft'].append(self.spacecraft['pos'].copy())
        
        # Log detailed data
        self.log_simulation_data(current_time)
    
    def calculate_orbital_energy(self, body, central_mass, central_pos):
        """Calculate specific orbital energy"""
        r = np.linalg.norm(body['pos'] - central_pos)
        v = np.linalg.norm(body['vel'])
        return 0.5 * v**2 - self.G * central_mass / r
    
    def get_orbital_elements(self, body, central_body):
        r_vec = body['pos'] - central_body['pos']
        v_vec = body['vel'] - central_body['vel']

        # Convert to 3D vectors
        r_vec_3d = np.array([r_vec[0], r_vec[1], 0.0])
        v_vec_3d = np.array([v_vec[0], v_vec[1], 0.0])

        r = np.linalg.norm(r_vec)
        v = np.linalg.norm(v_vec)

        # Specific angular momentum
        h_vec = np.cross(r_vec_3d, v_vec_3d)
        h = np.linalg.norm(h_vec)

        # Semi-major axis
        mu = self.G * central_body['mass']
        energy = 0.5 * v**2 - mu / r
        a = -mu / (2 * energy) if energy < 0 else float('inf')

        # Eccentricity vector
        e_vec = (np.cross(v_vec_3d, h_vec) / mu) - (r_vec_3d / r)
        e = np.linalg.norm(e_vec)

        return {'a': a, 'e': e, 'h': h, 'energy': energy}

    
    def log_simulation_data(self, time_days):
        """Log detailed simulation data for analysis"""
        # Basic data
        self.data_log['time'].append(time_days)
        self.data_log['spacecraft_pos'].append(self.spacecraft['pos'].copy())
        self.data_log['spacecraft_vel'].append(self.spacecraft['vel'].copy())
        
        # Orbital energy
        energy = self.calculate_orbital_energy(self.spacecraft, self.sun['mass'], self.sun['pos'])
        self.data_log['orbital_energy'].append(energy)
        
        # Distances
        self.data_log['distance_sun'].append(np.linalg.norm(self.spacecraft['pos'] - self.sun['pos']))
        self.data_log['distance_earth'].append(np.linalg.norm(self.spacecraft['pos'] - self.earth['pos']))
        self.data_log['distance_mars'].append(np.linalg.norm(self.spacecraft['pos'] - self.mars['pos']))
        self.data_log['distance_jupiter'].append(np.linalg.norm(self.spacecraft['pos'] - self.jupiter['pos']))
        
        # Velocity magnitude
        self.data_log['velocity_magnitude'].append(np.linalg.norm(self.spacecraft['vel']))
        
        # Orbital elements
        elements = self.get_orbital_elements(self.spacecraft, self.sun)
        self.data_log['orbital_elements'].append(elements)
    
    def generate_lab_report(self, filename=None):
        """Generate comprehensive plots for lab report"""
        if not filename:
            filename = f"orbital_simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 24))
        
        # Convert data to numpy arrays for easier plotting
        times = np.array(self.data_log['time'])
        positions = np.array(self.data_log['spacecraft_pos'])
        velocities = np.array(self.data_log['spacecraft_vel'])
        energies = np.array(self.data_log['orbital_energy'])
        
        # Plot 1: Orbital trajectory
        ax1 = plt.subplot(4, 2, 1)
        ax1.plot(positions[:, 0] / self.AU, positions[:, 1] / self.AU, 'k-', linewidth=2, label='Spacecraft')
        
        # Add planetary orbits
        earth_traj = np.array(self.trajectories['earth'])
        mars_traj = np.array(self.trajectories['mars'])
        jupiter_traj = np.array(self.trajectories['jupiter'])
        
        ax1.plot(earth_traj[:, 0] / self.AU, earth_traj[:, 1] / self.AU, 'b-', alpha=0.5, label='Earth')
        ax1.plot(mars_traj[:, 0] / self.AU, mars_traj[:, 1] / self.AU, 'r-', alpha=0.5, label='Mars')
        ax1.plot(jupiter_traj[:, 0] / self.AU, jupiter_traj[:, 1] / self.AU, 'orange', alpha=0.5, label='Jupiter')
        
        # Mark burn locations
        for burn in self.data_log['burn_events']:
            ax1.plot(burn['position'][0] / self.AU, burn['position'][1] / self.AU, 'ro', markersize=8)
        
        ax1.plot(0, 0, 'yo', markersize=15, label='Sun')
        ax1.set_xlabel('X Position (AU)')
        ax1.set_ylabel('Y Position (AU)')
        ax1.set_title('Spacecraft Trajectory')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_aspect('equal')
        
        # Plot 2: Orbital Energy vs Time
        ax2 = plt.subplot(4, 2, 2)
        ax2.plot(times, energies / 1e6, 'g-', linewidth=2)
        ax2.set_xlabel('Time (days)')
        ax2.set_ylabel('Specific Orbital Energy (MJ/kg)')
        ax2.set_title('Orbital Energy Evolution')
        ax2.grid(True, alpha=0.3)
        
        # Mark burn events
        for burn in self.data_log['burn_events']:
            ax2.axvline(x=burn['time'], color='red', linestyle='--', alpha=0.7)
        
        # Plot 3: Distance vs Time
        ax3 = plt.subplot(4, 2, 3)
        ax3.plot(times, np.array(self.data_log['distance_sun']) / self.AU, 'y-', label='Sun')
        ax3.plot(times, np.array(self.data_log['distance_earth']) / self.AU, 'b-', label='Earth')
        ax3.plot(times, np.array(self.data_log['distance_mars']) / self.AU, 'r-', label='Mars')
        ax3.plot(times, np.array(self.data_log['distance_jupiter']) / self.AU, 'orange', label='Jupiter')
        ax3.set_xlabel('Time (days)')
        ax3.set_ylabel('Distance (AU)')
        ax3.set_title('Distances to Celestial Bodies')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.set_yscale('log')
        
        # Plot 4: Velocity Magnitude vs Time
        ax4 = plt.subplot(4, 2, 4)
        ax4.plot(times, self.data_log['velocity_magnitude'], 'm-', linewidth=2)
        ax4.set_xlabel('Time (days)')
        ax4.set_ylabel('Velocity Magnitude (m/s)')
        ax4.set_title('Spacecraft Velocity')
        ax4.grid(True, alpha=0.3)
        
        # Mark burn events
        for burn in self.data_log['burn_events']:
            ax4.axvline(x=burn['time'], color='red', linestyle='--', alpha=0.7)
        
        # Plot 5: Orbital Elements vs Time
        ax5 = plt.subplot(4, 2, 5)
        semi_major_axes = [elem['a'] for elem in self.data_log['orbital_elements'] if elem['a'] != float('inf')]
        eccentricities = [elem['e'] for elem in self.data_log['orbital_elements']]
        
        if semi_major_axes:
            ax5_twin = ax5.twinx()
            ax5.plot(times[:len(semi_major_axes)], np.array(semi_major_axes) / self.AU, 'b-', label='Semi-major axis')
            ax5_twin.plot(times[:len(eccentricities)], eccentricities, 'r-', label='Eccentricity')
            ax5.set_xlabel('Time (days)')
            ax5.set_ylabel('Semi-major axis (AU)', color='b')
            ax5_twin.set_ylabel('Eccentricity', color='r')
            ax5.set_title('Orbital Elements')
            ax5.grid(True, alpha=0.3)
        
        # Plot 6: Velocity Components
        ax6 = plt.subplot(4, 2, 6)
        ax6.plot(times, velocities[:, 0], 'r-', label='Vx')
        ax6.plot(times, velocities[:, 1], 'b-', label='Vy')
        ax6.set_xlabel('Time (days)')
        ax6.set_ylabel('Velocity (m/s)')
        ax6.set_title('Velocity Components')
        ax6.grid(True, alpha=0.3)
        ax6.legend()
        
        # Plot 7: Phase Space (Position vs Velocity)
        ax7 = plt.subplot(4, 2, 7)
        ax7.plot(np.array(self.data_log['distance_sun']) / self.AU, self.data_log['velocity_magnitude'], 'k-', alpha=0.7)
        ax7.set_xlabel('Distance from Sun (AU)')
        ax7.set_ylabel('Velocity Magnitude (m/s)')
        ax7.set_title('Phase Space Plot')
        ax7.grid(True, alpha=0.3)
        
        # Plot 8: Summary Statistics
        ax8 = plt.subplot(4, 2, 8)
        ax8.text(0.05, 0.95, f'Mission Summary:', fontsize=14, fontweight='bold', transform=ax8.transAxes)
        
        # Calculate statistics
        max_dist = max(self.data_log['distance_sun']) / self.AU
        min_dist = min(self.data_log['distance_sun']) / self.AU
        max_vel = max(self.data_log['velocity_magnitude'])
        min_vel = min(self.data_log['velocity_magnitude'])
        total_delta_v = sum([burn['magnitude'] for burn in self.data_log['burn_events']])
        
        stats_text = f"""
Total Mission Time: {times[-1]:.1f} days
Total ΔV Used: {total_delta_v:.0f} m/s
Number of Burns: {len(self.data_log['burn_events'])}

Orbital Statistics:
Maximum Distance from Sun: {max_dist:.2f} AU
Minimum Distance from Sun: {min_dist:.2f} AU
Maximum Velocity: {max_vel:.0f} m/s
Minimum Velocity: {min_vel:.0f} m/s

Burn Events:"""
        
        for i, burn in enumerate(self.data_log['burn_events']):
            stats_text += f"\nBurn {i+1}: {burn['magnitude']:.0f} m/s at {burn['direction_deg']:.1f}° (Day {burn['time']:.1f})"
        
        ax8.text(0.05, 0.85, stats_text, fontsize=10, transform=ax8.transAxes, verticalalignment='top')
        ax8.set_xlim(0, 1)
        ax8.set_ylim(0, 1)
        ax8.axis('off')
        
        plt.tight_layout()
        plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{filename}.pdf", bbox_inches='tight')
        
        print(f"Lab report saved as {filename}.png and {filename}.pdf")
        return fig