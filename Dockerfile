FROM nginx:alpine
LABEL maintainer="lonelyion@outlook.com"
WORKDIR /app
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories && \
    \
    echo "**** installing Python ****" && \
    apk add python3 && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    \
    echo "**** installing pip ****" && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    \
    echo "**** installing applications ****" &&\
    apk add unzip supervisor chromium chromium-chromedriver && \
    \
    echo "**** installing fonts ****" && \
    wget https://github.91chifun.workers.dev//https://github.com/lonelyion/TweetToBot-Docker/releases/download/font/noto-sans.zip && \
    unzip noto-sans.zip -d /usr/share/fonts/ && \
    chmod 644 /usr/share/fonts/noto-sans && \
    fc-cache -fv && \
    echo "**** post installation ****" && \
    rm noto-sans.zip && \
    apk del unzip && \
    echo "Done"

ADD ./ /app/

RUN echo "**** installing dependencies ****" && \
    pip3 install -r requirements.txt && \
    \
    echo "**** setting up nginx ****" && \
    rm /usr/share/nginx/html -rf && \
    mkdir -p /app/cache/transtweet/transimg/ && \
    chmod -R 644 /app/cache/transtweet/transimg && \
    rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf && \
    cp /app/conf/nginx.conf /etc/nginx/nginx.conf && \
    cp /app/conf/nginx_default.conf /etc/nginx/conf.d/default.conf && \
    \
    echo "**** setting up supervisord ****" && \
    mkdir -p /etc/supervisor/conf.d/ && \
    cp /app/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8091 80

CMD ["/usr/bin/supervisord"]