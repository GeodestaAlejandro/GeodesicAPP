import math

class CoordinateNormalizer:

    @staticmethod
    def normalize(input_data):

        coord_type = input_data.type
        values = input_data.values

        if coord_type == "geodetic":
            return CoordinateNormalizer._normalize_geodetic(values)

        elif coord_type == "ecef":
            return CoordinateNormalizer._normalize_ecef(values)

        elif coord_type == "parametric":
            return CoordinateNormalizer._normalize_parametric(values)

        else:
            raise ValueError("Tipo no soportado")
        
    @staticmethod
    def _normalize_geodetic(values):
  
        lat = math.radians(values["lat"])
        lon = math.radians(values["lon"])
        h = float(values.get("h", 0))

        return {
            "type": "geodetic",
            "lat": lat,
            "lon": lon,
            "h": h
        }
    
    @staticmethod
    def _normalize_ecef(values):

        return {
            "type": "ecef",
            "x": float(values["x"]),
            "y": float(values["y"]),
            "z": float(values["z"])
        }
    
    @staticmethod
    def _normalize_parametric(values):

        beta = math.radians(values["beta"])
        lon = math.radians(values["lon"])

        return {
            "type": "parametric",
            "beta": beta,
            "lon": lon
        }