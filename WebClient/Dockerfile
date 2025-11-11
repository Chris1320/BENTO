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
# Use .env.prod if it exists, otherwise use .env
RUN if [ -f .env.prod ]; then cp .env.prod .env; fi
RUN bun run build

# Stage 3: Set up the production environment
FROM oven/bun:1.2.17-alpine AS production
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# Copy the entire built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 8080

# Start the web client using npm run start
ENV PORT=8080
CMD ["bun", "run", "start"]
