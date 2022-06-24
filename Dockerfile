# CloudSync - Auth Server
# Flask + MongoDB - on Gunicorn
# Dockerfile

# Using Alpine's official image, latest version
FROM alpine:3.16.0

# Installing Python and other required packages
RUN apk add --no-cache build-base python3 python3-dev py3-wheel py3-pip jpeg-dev zlib-dev

COPY requirements.txt /root/
RUN pip install -r /root/requirements.txt

# Preparing container
# User and directory structure creation
RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    mkdir /home/appuser/logs && \
    mkdir /home/appuser/src && \
    mkdir /home/appuser/tests && \
    mkdir /home/appuser/templates
# Creating log file
RUN touch /home/appuser/logs/auth_server.log
# Setting environment
ENV HOME=/home/appuser
USER appuser
# Copying files
COPY auth_server.py gunicorn_config.py /home/appuser/
COPY src /home/appuser/src
COPY templates /home/appuser/templates
COPY tests /home/appuser/tests
# Configuring network and launching server
WORKDIR /home/appuser/
EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn_config.py", "auth_server:app"]
