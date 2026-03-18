import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"

export const authOptions: NextAuthOptions = {
  // Prisma adapter yok — DB gerektirmez, JWT cookie'de saklanır
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          access_type: "offline",
          prompt: "consent",
          scope: [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/adwords",
          ].join(" "),
        },
      },
    }),
  ],

  session: {
    strategy: "jwt",
  },

  callbacks: {
    async jwt({ token, account }) {
      // İlk Google girişinde access_token'ı token'a ekle
      if (account?.access_token) {
        token.accessToken = account.access_token
      }
      return token
    },

    async session({ session, token }) {
      // Client tarafında session.accessToken okunabilsin
      session.accessToken = token.accessToken as string
      return session
    },
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },
}
