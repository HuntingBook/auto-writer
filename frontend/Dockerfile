FROM node:20-alpine AS builder

WORKDIR /app

ARG AUTO_WRITER_API_BASE_URL=""
ENV AUTO_WRITER_API_BASE_URL=$AUTO_WRITER_API_BASE_URL

COPY package*.json ./
RUN npm config set registry https://registry.npmmirror.com
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
