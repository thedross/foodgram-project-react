from django.core.exceptions import ValidationError


class FoodgramUserValidator:
    @staticmethod
    def validate_username(value):
        if value == "me":
            raise ValidationError("Никнейм 'me' недопустим")
