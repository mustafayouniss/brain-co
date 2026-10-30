import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const COOKIE_NAME = "backend_token";

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get(COOKIE_NAME)?.value;
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const backendResponse = await fetch(`${BACKEND_API_URL}/ring1/capabilities`, {
      method: "GET",
      headers,
    });

    if (!backendResponse.ok) {
      const err = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(err, { status: backendResponse.status });
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch Ring 1 capabilities", details: String(error) },
      { status: 500 }
    );
  }
}
