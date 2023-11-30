FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
#  "" Для локального запуска. ""
# CMD ["python", "manage.py", "runserver", "0:8000"] 