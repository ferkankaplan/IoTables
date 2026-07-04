FROM node:25-alpine

WORKDIR /app

RUN npm install -g pnpm@11.0.0

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json ./frontend/package.json
RUN pnpm install --frozen-lockfile --filter @iotables/frontend...

COPY frontend ./frontend

EXPOSE 5173

CMD ["pnpm", "--dir", "frontend", "dev", "--host", "0.0.0.0"]
