FROM node:22-alpine

WORKDIR /app

# NEXT_PUBLIC_* values are embedded by Next.js during the production build for browser execution.
# Browser-side requests from host connect via localhost:8000.
# Server-side requests inside Docker container connect via INTERNAL_BACKEND_URL (http://backend:8000).
ARG NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
ENV NODE_ENV=production \
    INTERNAL_BACKEND_URL=http://backend:8000 \
    NEXT_PUBLIC_BACKEND_API_URL=${NEXT_PUBLIC_BACKEND_API_URL} \
    NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}

COPY package.json package-lock.json ./

RUN npm ci --include=dev

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
