import csv
import os
from builtins import FileNotFoundError

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    """Загрузка тегов в БД."""

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'data/tags.csv')

        self.stdout.write('Началась загрузка тегов в БД...')

        try:
            with open(file_path, 'r', encoding='UTF-8') as tags:
                for name, color, slug in csv.reader(tags):
                    Tag.objects.get_or_create(
                        name=name,
                        color=color,
                        slug=slug
                    )
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Файл tags.csv не найден'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при чтении файла тегов: {str(e)}')
            )

        self.stdout.write(self.style.SUCCESS(
            'Данные о тегах успешно добавлены в БД')
        )
