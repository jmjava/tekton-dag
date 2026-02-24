#!/usr/bin/env bash
# Install PHP 8.3+ and Composer for local dev (e.g. to build tekton-dag-php).
# Run this script with sudo, or run the commands below manually.
#
# Usage: sudo ./scripts/install-php-local.sh
#    Or: run the apt and composer commands below yourself.
set -euo pipefail

echo "Installing PHP and extensions..."
apt-get update -qq
apt-get install -y -qq \
  php-cli \
  php-xml \
  php-mbstring \
  php-curl \
  php-zip \
  unzip

# Optional: PHP 8.3 on Ubuntu 22.04/24.04 via ondrej/php PPA
if ! php -r 'exit(version_compare(PHP_VERSION, "8.3.0", ">=") ? 0 : 1);' 2>/dev/null; then
  echo "PHP version is below 8.3. Adding ondrej/php PPA for PHP 8.3..."
  apt-get install -y -qq software-properties-common
  add-apt-repository -y ppa:ondrej/php
  apt-get update -qq
  apt-get install -y -qq php8.3-cli php8.3-xml php8.3-mbstring php8.3-curl php8.3-zip
  update-alternatives --set php /usr/bin/php8.3 2>/dev/null || true
fi

echo "Installing Composer to /usr/local/bin..."
curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

echo "Done. php --version && composer --version"
php --version
composer --version
