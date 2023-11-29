"""Загрузка json-файла из папки /data/."""
import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):

        with open('data/ingredients.json', encoding='utf-8') as file:
            data = json.load(file)
            for i in data:
                name = i['name']
                measurement_unit = i['measurement_unit']
                try:
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit,
                    )
                    if created:
                        ingredient.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Ингредиент {name} сохранен в базе!'
                            )
                        )
                    else:
                        self.stderr.write(
                            self.style.NOTICE(
                                f'Ингредиент {name} уже есть в базе!'
                            )
                        )
                except Exception as error:
                    self.stderr.write(self.style.WARNING(f'{error}'))
                    raise Exception(error)
            self.stdout.write(
                self.style.SUCCESS('Данные успешно загружены')
            )
