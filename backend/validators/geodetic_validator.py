from base_validator import BaseValidator

class GeodeticValidator(BaseValidator):

    def validate(self, values: dict):
        lat = values.get("lat")
        lon = values.get("lon")
        h = values.get("h")

        if h < -500 or h > 10000:
            print("Advertencia: altura fuera de rango típico")

        if lat is None or lon is None:
            raise ValueError("Latitud y longitud son obligatorias")

        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitud inválida: {lat}")

        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitud inválida: {lon}")

        if h is not None and not isinstance(h, (int, float)):
            raise ValueError("Altura debe ser numérica")

        return True