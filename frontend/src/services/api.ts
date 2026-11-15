import type { ApiEnvelope, ComparisonSummary, IntensityPeriod, RegionSnapshot } from "../types";

const API = "/api/v1";

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API}${path}`, { headers: { Accept: "application/json" } });
  } catch {
    throw new ApiError("The application API could not be reached. Check that the backend is running.", 0);
  }
  if (!response.ok) {
    let message = `The request failed (${response.status}).`;
    try {
      const body = await response.json();
      message = body.error?.message ?? message;
    } catch {
      // Keep the safe status-based message when a proxy returns non-JSON content.
    }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  return search.size ? `?${search.toString()}` : "";
}

export const api = {
  current: () => getJson<ApiEnvelope<IntensityPeriod[]>>("/carbon-intensity/current"),
  forecast: (hours = 24) => getJson<ApiEnvelope<IntensityPeriod[]>>(`/carbon-intensity/forecast${query({ hours })}`),
  history: (start: string, end: string, regionId?: number) =>
    getJson<ApiEnvelope<IntensityPeriod[]>>(`/carbon-intensity/history${query({ start, end, region_id: regionId })}`),
  regions: () => getJson<ApiEnvelope<RegionSnapshot[]>>("/regions"),
  regionCurrent: (regionId: number) => getJson<ApiEnvelope<IntensityPeriod[]>>(`/regions/${regionId}/current`),
  regionHistory: (regionId: number, start: string, end: string) =>
    getJson<ApiEnvelope<IntensityPeriod[]>>(`/regions/${regionId}/history${query({ start, end })}`),
  postcode: (postcode: string) => getJson<ApiEnvelope<IntensityPeriod[]>>(`/postcodes/${encodeURIComponent(postcode)}/carbon-intensity`),
  regionalComparison: (ids: number[], start: string, end: string) => {
    const search = new URLSearchParams();
    ids.forEach((id) => search.append("region_ids", String(id)));
    search.set("start", start);
    search.set("end", end);
    return getJson<ApiEnvelope<ComparisonSummary[]>>(`/statistics/regional-comparison?${search.toString()}`);
  },
  sources: () => getJson<ApiEnvelope<Array<Record<string, string>>>>("/data-sources"),
};

export function downloadCsv(periods: IntensityPeriod[], filename = "carbon-intensity.csv") {
  const columns = ["from_utc", "to_utc", "region_id", "region_name", "actual_gco2_kwh", "forecast_gco2_kwh", "neso_index"];
  const rows = periods.map((item) => [
    item.from,
    item.to,
    item.region_id,
    item.region_name,
    item.actual ?? "",
    item.forecast ?? "",
    item.index ?? "",
  ]);
  const escape = (value: unknown) => `"${String(value).replaceAll('"', '""')}"`;
  const csv = [columns, ...rows].map((row) => row.map(escape).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
