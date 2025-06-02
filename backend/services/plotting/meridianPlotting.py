
import matplotlib  
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import math  
  
def xz_ellipse_from_lat(a, b, lat_deg):  
    rad = math.radians(lat_deg)  
    return a * math.cos(rad), b * math.sin(rad)  
  
def plot_meridian_ellipse_and_points(a, b, points, point_labels):
    #x-position of the center
    u=0.
    v=0.
    t = np.linspace(0, 2*np.pi, 100)
    ellipse_x = u + a * np.cos(t)
    ellipse_z = v + b * np.sin(t)
    plt.figure(figsize=(6, 8))
    plt.plot(ellipse_x, ellipse_z, label='Elipse Meridiana', color='red')
    plt.axhline(0, color='black', linewidth=1, linestyle='--')
    plt.axvline(0, color='black', linewidth=1, linestyle='--')
    offsets = [(2500000, 2500000), (2500000, -2500000), (-2500000, -2500000)]
    for (x, z), label, (dx, dz) in zip(points, point_labels, offsets):
        plt.plot(x, z, 'o', markersize=5, label=label)
        plt.text(x + dx, z + dz, f"({x:.2f}, {z:.2f})", fontsize=8, ha='center', va='center',
         bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.6, lw=0.5))
        plt.plot([x, x + dx], [z, z + dz], color='gray', linestyle='--', linewidth=0.5)
        plt.axis('equal')
    plt.xlabel('X (m)')
    plt.ylabel('Z (m)')
    plt.title('Puntos sobre la elipse meridiana')
    plt.legend()

    # plt.axis('equal')
    lim_x = 1.1 * a
    lim_z = 1.1 * b
    plt.xlim(-lim_x, lim_x)
    plt.ylim(-lim_z, lim_z)

    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()


    # Memoria hecha para no usar almacenamietno de mi pc.
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

