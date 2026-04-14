from .geodetic_validator import GeodeticValidator
from .ecef_validator import ECEFValidator
from .parametric_validator import ParametricValidator

class ValidatorFactory:

    @staticmethod
    def get_validator(coord_type: str):

        if coord_type == "geodetic":
            return GeodeticValidator()

        elif coord_type == "ecef":
            return ECEFValidator()

        elif coord_type == "parametric":
            return ParametricValidator()

        else:
            raise ValueError("Tipo de coordenada no soportado")