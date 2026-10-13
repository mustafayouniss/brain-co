import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/backend-auth";

/**
 * GET /api/auth/session — current session from backend JWT.
 * 
 * This endpoint validates the stored backend token and returns the user profile
 * from the backend /auth/me endpoint.
 */
export async function GET(request: NextRequest) {
  // Get token from Authorization header (preferred) or cookie (fallback)
  const authHeader = request.headers.get("Authorization");
  const token = authHeader?.replace("Bearer ", "") || request.cookies.get("backend_token")?.value;

  if (!token) {
    return NextResponse.json({ user: null });
  }

  try {
    const user = await getCurrentUser(token);
    return NextResponse.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.full_name,
        role: user.role,
        is_active: user.is_active,
      },
    });
  } catch (error) {
    // Token is invalid or expired
    return NextResponse.json({ user: null });
  }
}
