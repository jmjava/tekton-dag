# PHP/Composer build image. Needs zip ext for Composer; task script needs jq to parse JSON.
# Build variants:
#   docker build --build-arg PHP_VERSION=8.1 -t ...:php81 -f Dockerfile.php .
#   docker build --build-arg PHP_VERSION=8.2 -t ...:php82 -f Dockerfile.php .
ARG PHP_VERSION=8.3
FROM php:${PHP_VERSION}-cli
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends libzip-dev zlib1g-dev jq \
    && docker-php-ext-install zip \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN php -v | head -1 && composer -V 2>&1 | head -1
