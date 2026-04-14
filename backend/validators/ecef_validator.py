from base_validator import BaseValidator

class ECEFValidator(BaseValidator):

    def validate(self, values: dict):
        x = values.get("x")
        y = values.get("y")
        z = values.get("z")

        if None in (x, y, z):
            raise ValueError("X, Y, Z son obligatorios")

        for val in (x, y, z):
            if not isinstance(val, (int, float)):
                raise ValueError("Coordenadas deben ser numéricas")

        return True