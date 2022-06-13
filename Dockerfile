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
    useradd -m authuser && \
    mkdir /home/authuser/logs && \
    mkdir /home/authuser/src && \
    mkdir /home/authuser/tests && \
    mkdir /home/authuser/templates
# Creating log file
RUN touch /home/authuser/logs/auth_server.log
# Setting environment
ENV HOME=/home/authuser
USER authuser
# Copying files
COPY auth_server.py gunicorn_config.py /home/authuser/
COPY src /home/authuser/src
COPY templates /home/authuser/templates
COPY tests /home/authuser/tests
# Configuring network and launching server
WORKDIR /home/authuser/
EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn_config.py", "auth_server:app"]
