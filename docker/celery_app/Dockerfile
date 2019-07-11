FROM python:3

WORKDIR /usr/src/app
COPY requirements.txt ./
COPY entrypoint.sh /var/run
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

#CMD [ "ls","/var/run" ]
CMD [ "/bin/sh","/var/run/entrypoint.sh" ]