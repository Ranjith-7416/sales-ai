# Build stage
FROM node:20-alpine AS builder

ARG VITE_API_URL=http://localhost:8000/api
ARG VITE_API_TOKEN=
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_TOKEN=$VITE_API_TOKEN

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies. The repository currently does not commit a lockfile.
RUN npm install

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install serve to run the application
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:5173', (r) => {r.resume(); r.on('end', () => process.exit(r.statusCode === 200 ? 0 : 1));}).on('error', () => process.exit(1))"

# Start application
CMD ["serve", "-s", "dist", "-l", "5173"]
