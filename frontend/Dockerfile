# ---- Stage 1: React build ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Stage 2: nginx (non-root)----
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
# CRA -> /app/build   |   Vite -> /app/dist 
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080