# Imagen de la API (Node 22 + Prisma)
FROM node:22-slim

# Prisma necesita OpenSSL para conectarse a PostgreSQL
RUN apt-get update -y && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Dependencias (se cachean mientras package*.json no cambie).
#    npm ci corre "prisma generate" (postinstall); necesita una DATABASE_URL
#    cualquiera solo para leer la configuración: no se conecta.
COPY package*.json prisma.config.js ./
COPY prisma ./prisma
RUN DATABASE_URL="postgresql://build:build@localhost:5432/build" npm ci

# 2. Código de la API
COPY src ./src

EXPOSE 3000

# Al arrancar: crea/actualiza las tablas, asegura el admin y levanta la API
CMD ["sh", "-c", "npx prisma migrate deploy && npm run seed && npm start"]
