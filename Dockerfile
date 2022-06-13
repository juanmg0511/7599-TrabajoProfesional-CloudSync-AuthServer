# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Dockerfile

# Using Ubuntu's official image, latest LTS version
FROM ubuntu:20.04

# Avoiding stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive
# Installing Python
RUN apt-get update && \
    apt-get install --no-install-recommends -y python3 python3-dev python3-venv python3-pip python3-wheel libevent-dev build-essential && \
	apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Preparing container
# Requirements and directory structure creation
COPY requirements.txt /root/
RUN pip install -r /root/requirements.txt && \
    useradd -m ubuntu && \
    mkdir /home/ubuntu/logs && \
    mkdir /home/ubuntu/src && \
    mkdir /home/ubuntu/tests && \
    mkdir /home/ubuntu/templates
# Creating log file
RUN touch /home/ubuntu/logs/auth_server.log
# Setting environment
ENV HOME=/home/ubuntu
USER ubuntu
# Copying files
COPY auth_server.py gunicorn_config.py /home/ubuntu/
COPY src /home/ubuntu/src
COPY templates /home/ubuntu/templates
COPY tests /home/ubuntu/tests
# Configuring network and launching server
WORKDIR /home/ubuntu/
EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn_config.py", "auth_server:app"]
