FROM python:3.12.0-alpine3.18
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

# Setup SSH with secure root login
RUN apk add openssh netcat-openbsd \
 && mkdir /var/run/sshd \
 && echo 'root:password' | chpasswd \
 && sed -i 's/\#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
EXPOSE 22

RUN ssh-keygen -A

RUN apk add git build-base binutils linux-headers libffi-dev
RUN apk add proj proj-dev proj-util gdal gdal-dev
RUN apk add openblas-dev
RUN apk add geos-dev

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

COPY requirements-dev.txt /usr/src/app/
RUN pip install -r requirements-dev.txt

CMD ["/usr/sbin/sshd", "-D"]
