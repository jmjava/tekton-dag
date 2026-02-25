# PHP/Composer build image for tekton-dag.
# PHP 8.3 (ondrej PPA) + Composer; includes jq/curl for task scripts.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y -qq \
    curl \
    jq \
    ca-certificates \
    software-properties-common \
    && add-apt-repository -y ppa:ondrej/php \
    && apt-get update -qq \
    && apt-get install -y -qq \
    php8.3-cli \
    php8.3-mbstring \
    php8.3-xml \
    php8.3-curl \
    php8.3-zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

RUN php -v | head -1 && composer -V 2>&1 | head -1
