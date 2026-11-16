import { NextResponse } from "next/server";
import { getServerBackendApiUrl } from "@/lib/server-backend-url";

export async function GET() {
  try {
    const res = await fetch(`${getServerBackendApiUrl()}/health/db`, {
      method: "GET",
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json({
        status: "degraded",
        backend: "connected",
        database: "unreachable",
        engines_count: 6,
        ring: "Ring 1",
      });
    }

    const data = await res.json();
    return NextResponse.json({
      status: "healthy",
      backend: "connected",
      database: data.database || "up",
      engines_count: 6,
      ring: "Ring 1",
      capabilities: [
        "perception.structure_input",
        "observation.record_event",
        "context.resolve",
        "memory.store_record",
        "retrieval.query",
        "planning.create_plan",
      ],
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: "offline",
        backend: "disconnected",
        database: "unknown",
        engines_count: 0,
        ring: "Ring 1",
        error: String(error),
      },
      { status: 503 }
    );
  }
}
