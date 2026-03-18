import { PrismaClient } from "@prisma/client"

declare global {
  // eslint-disable-next-line no-var
  var __prisma: PrismaClient | undefined
}

/**
 * Prisma client'ı sadece ilk kez kullanıldığında başlatır.
 * Build sırasında modül yüklenirken değil, gerçek istek geldiğinde çalışır.
 */
function getPrismaClient(): PrismaClient {
  if (!global.__prisma) {
    global.__prisma = new PrismaClient()
  }
  return global.__prisma
}

// Proxy ile lazy initialization — erişim anında başlatılır
export const prisma = new Proxy({} as PrismaClient, {
  get(_, prop: string | symbol) {
    return (getPrismaClient() as unknown as Record<string | symbol, unknown>)[prop]
  },
})
