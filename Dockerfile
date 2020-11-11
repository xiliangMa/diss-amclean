FROM arm64v8/alpine:3.12
#FROM alpine:3.12

RUN set -eux; 

### 1 -- change repository source
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
#RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.huaweicloud.com/g' /etc/apk/repositories

### 2 -- add tools and libs
RUN apk update
RUN apk add --no-cache clamav
RUN apk add python3
RUN apk add --upgrade clamav-libunrar

RUN apk add py-pip
RUN pip install docker==4.2.0


### 3 -- copy file and set permission
COPY ./amclean/*  /usr/bin/
COPY ./etc/crontabs /etc/crontabs
COPY ./etc/periodic  /etc/periodic

RUN chmod +x /usr/bin/*
RUN mkdir /var/run/clamav
RUN chmod a+w /var/run/clamav/

CMD /usr/bin/amclean

