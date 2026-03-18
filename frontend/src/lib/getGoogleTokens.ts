import { prisma } from "@/lib/prisma"

/**
 * Arka plan ajanı için kullanıcının Google token'larını DB'den getirir.
 *
 * Kullanım (backend agent'ı API route üzerinden çağırır):
 *   const tokens = await getGoogleTokens(userId)
 *   // tokens.accessToken  → GA4 ve Google Ads API çağrıları için
 *   // tokens.refreshToken → token süresi dolunca yenilemek için
 */
export async function getGoogleTokens(userId: string) {
  const account = await prisma.account.findFirst({
    where: {
      userId,
      provider: "google",
    },
    select: {
      access_token: true,
      refresh_token: true,
      expires_at: true,
    },
  })

  if (!account) {
    throw new Error(`Kullanıcı ${userId} için Google hesabı bulunamadı`)
  }

  return {
    accessToken: account.access_token,
    refreshToken: account.refresh_token,
    expiresAt: account.expires_at,
    isExpired: account.expires_at
      ? Date.now() > account.expires_at * 1000
      : true,
  }
}
