import numpy as np  
import matplotlib.pyplot as plt  
from mpl_toolkits.mplot3d import Axes3D  
  
# Simulamos malla de alturas del geoide en metros (¡esto es un ejemplo sintético!)  
lat = np.linspace(-90, 90, 180)  
lon = np.linspace(-180, 180, 360)  
lat_grid, lon_grid = np.meshgrid(lat, lon)  
  
# Onda artificial (no real, solo para mostrar cómo se ve)  
N = 30 * np.sin(3 * np.radians(lat_grid)) * np.cos(2 * np.radians(lon_grid))  
  
# ----------- GRÁFICO 2D ---------  
plt.figure(figsize=(12, 5))  
plt.imshow(N, extent=[-180, 180, -90, 90], cmap="RdBu_r", origin="lower")  
plt.title("Altura del geoide simulada (N, metros) respecto al elipsoide")  
plt.xlabel("Longitud")  
plt.ylabel("Latitud")  
plt.colorbar(label="Ondulación [m]")  
plt.show()  
  
# ----------- GRÁFICO 3D ---------  
fig = plt.figure(figsize=(10, 6))  
ax = fig.add_subplot(111, projection='3d')  
resample = (slice(None, None, 6), slice(None, None, 6))  # Baja resolución para ser más rápido  
ax.plot_surface(lon_grid[resample], lat_grid[resample], N[resample], cmap="RdBu_r")  
ax.set_title("Malla de ondulación del geoide (simulada)")  
ax.set_xlabel("Longitud")  
ax.set_ylabel("Latitud")  
ax.set_zlabel("Ondulación, m")  
plt.show()