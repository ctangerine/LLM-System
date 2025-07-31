# syntax=docker/dockerfile:1

ARG NODE_VERSION=22.17.0

FROM node:${NODE_VERSION}-alpine

# Use development node environment for Next.js
ENV NODE_ENV=development

WORKDIR /usr/src/app

# Copy package files and install dependencies as root first
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Create .next directory and set proper ownership
RUN mkdir -p .next && \
    chown -R node:node /usr/src/app && \
    chmod -R 755 /usr/src/app

# Switch to non-root user
USER node

# Expose the port that Next.js dev server uses
EXPOSE 3000

# Run Next.js in development mode
CMD ["npm", "run", "dev"]