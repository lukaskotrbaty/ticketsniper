# Stage 1: Base - Install dependencies
FROM node:18-alpine as base

# Install curl for health checks
RUN apk --no-cache add curl

WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies - This layer will be cached and reused
RUN npm install

# Stage 2: Builder - Build the Vue application for production
FROM base AS builder

# Copy the rest of the application code
# This needs to happen after npm install in the base stage
COPY . .

# Build the application for production
RUN npm run build

# Stage 3: Production - Serve the built assets with Nginx
FROM nginx:stable-alpine as production

# Install curl for health checks
RUN apk --no-cache add curl

# Remove default Nginx server configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration (will be created later)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from the builder stage
COPY --from=builder /usr/src/app/dist /usr/share/nginx/html

# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]

# Stage 4: Development - Run the Vite development server
FROM base AS development

# Copy the rest of the application code (needed for dev server)
# Note: This COPY is necessary here too, separate from the builder stage COPY,
# because the development stage needs the source code, not just the build artifacts.
COPY . .

# Expose the Vite dev server port
EXPOSE 8080

# Command to run the Vite development server
# --host allows connections from outside the container
CMD ["npm", "run", "dev", "--", "--host"]
