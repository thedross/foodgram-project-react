import csv
import os

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Importing Ingredients to DB"""

    def handle(self, *args, **kwargs):
        with open(
            os.path.join(settings.BASE_DIR, 'data/ingredients.csv'),
            'r',
            encoding='UTF-8'
        ) as ingredients:
            for row in csv.reader(ingredients):
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit,
                )
        self.stdout.write(self.style.SUCCESS('Данные успешно добавлены в БД'))
