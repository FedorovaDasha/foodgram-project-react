"""Загрузка json-файла из папки /data/."""

from django.core.management.base import BaseCommand
import json
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):

        with open('data/ingredients.json', encoding='utf-8') as file:
            data = json.load(file)
            id = 1
            for i in data:
                try:
                    i['id'] = id
                    ingredient = Ingredient(**i)
                # ingredient.name = i['name']
                # ingredient.measurement_unit = i['measurement_unit']
                    ingredient.save()
                    id += 1
                except Exception as error:
                    self.stderr.write(self.style.WARNING(f'{error}'))
                    raise Exception(error)
            self.stdout.write(
                self.style.SUCCESS('Successfully load data')
            )
