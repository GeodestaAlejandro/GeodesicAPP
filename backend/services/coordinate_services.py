from validators import validator_factory

class CoordinateService:

    @staticmethod
    def validate_coordinates(input_data):

        validator = validator_factory.get_validator(input_data.type)
        validator.validate(input_data.values)

        return {"status": "ok", "message": "Coordenadas válidas"}