FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Prisma client'ı generate et (auth.ts ve prisma.ts için gerekli)
RUN npx prisma generate

# Build sırasında NextAuth'un şikayet etmemesi için placeholder
ENV NEXTAUTH_SECRET=build-placeholder
ENV NEXTAUTH_URL=http://localhost:4000
ENV NEXT_PUBLIC_API_URL=http://localhost:3000

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
RUN mkdir -p ./public

EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
