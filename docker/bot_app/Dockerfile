FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

#CMD ["ls" , "-lah", "/usr/src/app" ]
CMD [ "python", "./bot_app.py" ]