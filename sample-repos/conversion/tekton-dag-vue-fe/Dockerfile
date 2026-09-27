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

# Serve with nginx. /propagation is proxied to the BFF so curl validation
# (and the SPA) see the original override header hop-to-hop.
FROM nginx:alpine
ENV BFF_UPSTREAM=http://release-lifecycle-demo
ENV NGINX_ENVSUBST_FILTER=BFF_UPSTREAM
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
