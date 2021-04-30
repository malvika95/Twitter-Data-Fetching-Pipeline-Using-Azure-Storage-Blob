FROM python:3.8.9-buster

WORKDIR /sender_module



COPY sender_module/requirements.txt .
RUN pip install -r requirements.txt

COPY /sender_module .


EXPOSE 8889
CMD ["python","-u", "manage.py","run"]

