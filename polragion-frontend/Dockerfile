# ============================================================================
# Build stage: install dependencies and produce the static Vite build
# ============================================================================
FROM node:22.17.1-alpine AS builder

WORKDIR /app

RUN npm install -g npm@11.6.2 \
    && node --version \
    && npm --version

# 1) Install dependencies first (cached as long as the lockfile is unchanged).
#    `npm ci` installs exactly what is pinned in package-lock.json.
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# 2) Copy the source and build the production bundle into /app/dist.
COPY . .
RUN npm run build

# ============================================================================
# Runtime stage: serve the static files with nginx
# ============================================================================
FROM nginx:1.27-alpine AS runtime

# Custom nginx config: SPA fallback, gzip and asset caching.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Only the compiled static assets end up in the final image.
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# nginx runs in the foreground so the container stays alive.
CMD ["nginx", "-g", "daemon off;"]
