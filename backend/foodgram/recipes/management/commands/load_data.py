import csv
import os
from builtins import FileNotFoundError

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка ингредиентов в БД."""

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'data/ingredients.csv')

        self.stdout.write('Началась загрузка данных...')

        try:
            with open(file_path, 'r', encoding='UTF-8') as ingredients:
                for name, measurement_unit in csv.reader(ingredients):
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit,
                    )
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                'Файл ingredients.csv не найден')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при чтении файла: {str(e)}')
            )

        self.stdout.write(self.style.SUCCESS(
            'Данные об ингредиентах успешно добавлены в БД')
        )
