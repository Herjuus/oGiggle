FROM node:22.2-alpine
WORKDIR /app
COPY ./package.json ./package.json
RUN npm i
COPY . .
RUN npm run build

ENTRYPOINT [ "node", "./build/index.js" ]