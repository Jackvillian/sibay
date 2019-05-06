FROM ubuntu:16.04
RUN  apt-get update && apt-get install -y ffmpeg supervisor curl net-tools vim
RUN mkdir -p /var/log/supervisord && touch /var/log/supervisord/supervisor.log && chmod -R 777 /var/log/supervisord
RUN touch /var/run/supervisor.sock && chmod 777 /var/run/supervisor.sock
COPY ffserver.conf /etc/ffserver.conf
COPY supervisor.conf /etc/supervisor/supervisor.conf
COPY translation.sh /etc/translation.sh
RUN chmod +x /etc/translation.sh
EXPOSE 8090 80
ENTRYPOINT /usr/bin/supervisord -n -c /etc/supervisor/supervisor.conf