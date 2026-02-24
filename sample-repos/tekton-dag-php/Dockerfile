FROM php:8.3-cli-alpine
WORKDIR /app
COPY . .
RUN composer install --no-dev --optimize-autoloader --no-interaction
EXPOSE 8080
CMD ["php", "-S", "0.0.0.0:8080", "-t", "public"]
