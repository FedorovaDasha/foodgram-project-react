# Продуктовый помощник «FOODGRAM»

## _Описание проекта:_

#### **_*Foodgram*_ - сервис для любителей кулинарии, который позволяет публиковать рецепты, сохранять избранные, подписываться на любимых авторов, а также формировать список покупок для выбранных рецептов в формате pdf.**


![This is an alt text.]( https://pictures.s3.yandex.net/resources/S16_01_1692340098.png "Foodgram - продуктовый помощник")


### _Технологии:_

* Django Rest Framework
* Python 3.9
* Nginx
* Gunicorn
* Docker
* PostgreSQL
* Djoser
* Pillow

### _Возможности проекта:_
* Регистрация пользователей
* Возможность добавления/редактирования/удаления своих рецептов
* Просмотр рецептов других пользователей
* Возможность добавления рецептов в избранное и в список покупок
* Формирование списка покупок с подсчетом количества ингредиентов
* Подписка на других пользователей 

### _Запуск проекта из образов с Docker hub_
- Для запуска необходимо создать папку проекта, например _foodgram_ и перейти в нее:
```
mkdir foodgram
cd foodgram
```
- В папку проекта скачиваем файл _docker-compose.production.yml_ и запускаем его:
```
sudo docker compose -f docker-compose.production.yml up
```
Произойдет скачивание образов, создание и включение контейнеров, создание томов и сети.
- Проверяем доступность проекта по адресу:

https://myfoodgrammm.sytes.net/

### _Запуск проекта локально из исходников GitHub_
- Клонируем себе репозиторий:
```
git clone git@github.com:FedorovaDasha/foodgram-project-react.git
```
- Выполняем запуск:
```
sudo docker compose -f docker-compose.yml up
```
- После запуска необходимо выполнить миграции и собрать статику бэкенда. Статика фронтенда собирается во время запуска контейнера, после чего он останавливается.
```
sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py migrate

sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py collectstatic

sudo docker compose -f [имя-файла-docker-compose.yml] exec backend cp -r /app/collected_static/. /backend_static/static/
```
- Необходимо загрузить список ингредиентов, запустив команду load_data:
```
sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py load_data data/ingredients.json
```
- Проверяем доступность проекта по адресу:

http://localhost:8000/

##
### _Демо-версия проекта:_
[Foodgram](https://myfoodgrammm.sytes.net)

### _Для просмотра панели администратора:_

e-mail: admin@mail.ru

password: Superadmin

##
Над проектом работала [FedorovaDasha](https://github.com/FedorovaDasha).

##