# Build stage
FROM node:22-alpine AS build
WORKDIR /app
ARG VITE_BAGGAGE_ENABLED=true
ARG VITE_BAGGAGE_ROLE=originator
ARG VITE_BAGGAGE_HEADER_NAME=x-dev-session
ARG VITE_BAGGAGE_KEY=dev-session
ENV VITE_BAGGAGE_ENABLED=$VITE_BAGGAGE_ENABLED \
    VITE_BAGGAGE_ROLE=$VITE_BAGGAGE_ROLE \
    VITE_BAGGAGE_HEADER_NAME=$VITE_BAGGAGE_HEADER_NAME \
    VITE_BAGGAGE_KEY=$VITE_BAGGAGE_KEY
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

# Serve with nginx. /propagation is answered on localhost by
# propagation_proxy.py, which copies the incoming override into the hop
# report and nests the BFF response.
FROM nginx:alpine
ENV BFF_UPSTREAM=http://release-lifecycle-demo
ENV APP_NAME=demo-fe
ENV BAGGAGE_HEADER_NAME=x-dev-session
ENV BAGGAGE_KEY=dev-session
RUN apk add --no-cache python3
COPY propagation_proxy.py /usr/local/bin/propagation_proxy.py
COPY nginx.conf.template /etc/nginx/conf.d/default.conf
COPY docker-entrypoint-wrap.sh /docker-entrypoint-wrap.sh
RUN chmod +x /docker-entrypoint-wrap.sh
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
ENTRYPOINT ["/docker-entrypoint-wrap.sh"]
CMD ["nginx", "-g", "daemon off;"]
