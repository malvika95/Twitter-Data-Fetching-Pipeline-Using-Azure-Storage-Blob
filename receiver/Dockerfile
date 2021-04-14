FROM python:3.8.9-buster

#Make a directory
WORKDIR /receiver_module

#copy requirements
COPY receiver_module/requirements.txt .

RUN pip install -r requirements.txt


COPY /receiver_module .

CMD ["python","src/receiver.py"]