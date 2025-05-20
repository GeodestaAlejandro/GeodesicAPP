import numpy as np
from models import GeodeticCoordinates, GeocentricCoordinates, ParametricCoordinates

# Constantes del modelo WGS84
WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563

class EllipsoidModel:
    def __init__(self, model="WGS84"):
        self.a = WGS84_A
        self.f = WGS84_F
        self.b = self.a * (1 - self.f)

    @property
    def e2(self):
        """Excentricidad al cuadrado."""
        return self.f * (2 - self.f)

    def geodetic_to_geocentric(self, geo: GeodeticCoordinates) -> GeocentricCoordinates:
        lat_rad = np.radians(geo.latitude)
        lon_rad = np.radians(geo.longitude)
        N = self.a / np.sqrt(1 - self.e2 * np.sin(lat_rad)**2)
        X = (N + geo.orthometric_height) * np.cos(lat_rad) * np.cos(lon_rad)
        Y = (N + geo.orthometric_height) * np.cos(lat_rad) * np.sin(lon_rad)
        Z = ((1 - self.f)**2 * N + geo.orthometric_height) * np.sin(lat_rad)
        return GeocentricCoordinates(X=X, Y=Y, Z=Z)

    def geocentric_to_geodetic(self, geo: GeocentricCoordinates) -> GeodeticCoordinates:
        X, Y, Z = geo.X, geo.Y, geo.Z
        p = np.sqrt(X**2 + Y**2)
        theta = np.arctan2(Z * self.a, p * self.b)
        lon = np.arctan2(Y, X)
        lat = np.arctan2(Z + self.e2 * self.b * np.sin(theta)**3, p - self.e2 * self.a * np.cos(theta)**3)
        N = self.a / np.sqrt(1 - self.e2 * np.sin(lat)**2)
        h = p / np.cos(lat) - N
        return GeodeticCoordinates(latitude=np.degrees(lat), longitude=np.degrees(lon), height=h)

    def parametric_to_geocentric(self, param: ParametricCoordinates) -> GeocentricCoordinates:
        X = self.a * np.cos(param.phi)
        Z = self.b * np.sin(param.phi)
        return GeocentricCoordinates(X=X, Y=0, Z=Z)

    def geocentric_to_parametric(self, geo: GeocentricCoordinates) -> ParametricCoordinates:
        theta = np.arctan2(geo.Z * self.a, geo.X * self.b)
        return ParametricCoordinates(phi=theta, lambda_=0, h=0)

def convert_coordinates(input_coords, input_system, output_system):
    ellipsoid = EllipsoidModel()

    if input_system == "geodetic":
        coords = GeodeticCoordinates(**input_coords)
        if output_system == "geocentric":
            return ellipsoid.geodetic_to_geocentric(coords)
        elif output_system == "parametric":
            geocentric = ellipsoid.geodetic_to_geocentric(coords)
            return ellipsoid.geocentric_to_parametric(geocentric)
        else:
            raise ValueError("Sistema de salida no válido para coordenadas geodésicas")

    elif input_system == "geocentric":
        coords = GeocentricCoordinates(**input_coords)
        if output_system == "geodetic":
            return ellipsoid.geocentric_to_geodetic(coords)
        elif output_system == "parametric":
            return ellipsoid.geocentric_to_parametric(coords)
        else:
            raise ValueError("Sistema de salida no válido para coordenadas geocéntricas")

    elif input_system == "parametric":
        coords = ParametricCoordinates(**input_coords)
        geocentric = ellipsoid.parametric