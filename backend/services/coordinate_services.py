from validators import validator_factory
from utils import coordinater_normalizer
class CoordinateService:

    @staticmethod
    def validate_coordinates(input_data):

        validator = validator_factory.get_validator(input_data.type)
        validator.validate(input_data.values)

        normalized = coordinater_normalizer.normalize(input_data)


        return {"status": "ok", "message": "Coordenadas válidas", "normalized": normalized
}
    
