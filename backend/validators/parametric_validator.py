from base_validator import BaseValidator

class ParametricValidator(BaseValidator):

    def validate(self, values: dict):
        beta = values.get("beta")
        lon = values.get("lon")

        if beta is None or lon is None:
            raise ValueError("Beta y longitud son obligatorias")

        if not (-90 <= beta <= 90):
            raise ValueError(f"Beta inválido: {beta}")

        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitud inválida: {lon}")

        return True