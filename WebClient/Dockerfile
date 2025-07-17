# Stage 1: Install dependencies
FROM oven/bun:1.2.17-alpine AS dependencies
WORKDIR /app
COPY ./package.json ./
COPY ./package-lock.json ./
COPY ./bun.lock ./
RUN bun install

# Stage 2: Build the web client
FROM oven/bun:1.2.17-alpine AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN bun run build

# Stage 3: Set up the production environment
FROM oven/bun:1.2.17-alpine AS production
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next/standalone ./standalone
COPY --from=builder /app/public /app/standalone/public
COPY --from=builder /app/.next/static /app/standalone/.next/static

EXPOSE 8080

# Start the web client
ENV PORT=8080
CMD ["node", "./standalone/server.js"]
