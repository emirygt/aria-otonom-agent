// NextAuth kaldırıldı — Google OAuth artık backend üzerinden yönetiliyor.
import { NextResponse } from "next/server"
export async function GET() { return NextResponse.json({ error: "not used" }, { status: 404 }) }
export async function POST() { return NextResponse.json({ error: "not used" }, { status: 404 }) }
