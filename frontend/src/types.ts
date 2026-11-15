export interface ApiMetadata {
  source: { provider: string; name: string; url: string; license: string };
  retrieved_at: string;
  timezone: string;
  stale: boolean;
  [key: string]: unknown;
}

export interface IntensityPeriod {
  from: string;
  to: string;
  region_id: number;
  region_name: string;
  region_type: string;
  provider_region_name?: string | null;
  forecast: number | null;
  actual: number | null;
  index: string | null;
  forecast_classification: string | null;
  actual_classification: string | null;
  generation_mix: Array<{ fuel: string; perc: number }>;
  postcode?: string | null;
}

export interface RegionSnapshot {
  id: number;
  name: string;
  short_name: string;
  type: string;
  available: boolean;
  current: IntensityPeriod | null;
}

export interface ApiEnvelope<T> {
  data: T;
  metadata: ApiMetadata;
}

export interface ComparisonSummary {
  region_id: number;
  region_name: string;
  count: number;
  average: number | null;
  minimum: number | null;
  maximum: number | null;
  current_forecast: number | null;
  trend_change: number | null;
}
