FROM ubuntu:16.04
WORKDIR /usr/src/app
RUN  apt-get update && apt-get install -y supervisor curl net-tools vim software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y build-essential python3.7 python3.7-dev python3-pip python3.7-venv
COPY requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /var/log/supervisord && touch /var/log/supervisord/supervisor.log && chmod -R 777 /var/log/supervisord
RUN touch /var/run/supervisor.sock && chmod 777 /var/run/supervisor.sock
COPY supervisor.conf /etc/supervisor/supervisor.conf
ENTRYPOINT /usr/bin/supervisord -n -c /etc/supervisor/supervisor.conf
