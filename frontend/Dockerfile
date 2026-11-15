FROM node:22-alpine

WORKDIR /app

# NEXT_PUBLIC_* values are embedded by Next.js during the production build.
# The backend URL must use the Compose service DNS name, not localhost.
ARG NEXT_PUBLIC_BACKEND_API_URL=http://backend:8000/api/v1
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
ENV NODE_ENV=production \
    NEXT_PUBLIC_BACKEND_API_URL=${NEXT_PUBLIC_BACKEND_API_URL} \
    NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}

COPY package.json package-lock.json ./

# Copy application source and any pre-existing local build artifacts if available
COPY . .

# If node_modules is not present in build context, install dependencies
RUN if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then \
        npm ci --include=dev ; \
    fi

# If .next is not pre-built in build context, execute Next.js production build
RUN if [ ! -d ".next" ] || [ ! -f ".next/BUILD_ID" ]; then \
        npm run build || npm run build ; \
    fi

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
