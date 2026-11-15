import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/backend-auth";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const COOKIE_NAME = "backend_token";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(COOKIE_NAME)?.value;

  if (!token) {
    return NextResponse.json(
      { error: "No session" },
      { status: 401 }
    );
  }

  try {
    const user = await getCurrentUser(token);
    return NextResponse.json({
      id: user.id,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      active_organization_id: user.active_organization_id,
      active_organization_name: user.active_organization_name,
      active_organization_slug: user.active_organization_slug,
      active_domain: user.active_domain,
      organizations: user.organizations || [],
    });
  } catch (error) {
    return NextResponse.json(
      { error: "Invalid session" },
      { status: 401 }
    );
  }
}
