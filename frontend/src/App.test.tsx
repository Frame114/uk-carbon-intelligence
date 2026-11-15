import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type { ApiEnvelope, IntensityPeriod, RegionSnapshot } from "./types";

const now = new Date();
const iso = (offsetMinutes = 0) => new Date(now.getTime() + offsetMinutes * 60_000).toISOString();

const point = (regionId = 18, actual: number | null = 88, forecast: number | null = 81): IntensityPeriod => ({
  from: iso(-30),
  to: iso(0),
  region_id: regionId,
  region_name: regionId === 18 ? "Great Britain" : "North Scotland",
  region_type: regionId === 18 ? "national" : "dno",
  actual,
  forecast,
  index: "low",
  actual_classification: "low",
  forecast_classification: "low",
  generation_mix: [{ fuel: "wind", perc: 47 }],
});

const region = (id = 18, name = "Great Britain"): RegionSnapshot => ({
  id,
  name,
  short_name: id === 18 ? "GB" : name,
  type: id === 18 ? "national" : "dno",
  available: true,
  current: point(id),
});

const envelope = <T,>(data: T): ApiEnvelope<T> => ({
  data,
  metadata: {
    source: { provider: "NESO", name: "NESO Carbon Intensity API", url: "https://api.carbonintensity.org.uk", license: "CC BY 4.0" },
    retrieved_at: iso(),
    timezone: "UTC",
    stale: false,
  },
});

function mockApi(reject = false) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    if (reject) throw new TypeError("offline");
    const url = String(input);
    let body: unknown;
    if (url.includes("/carbon-intensity/current")) body = envelope([point()]);
    else if (url.includes("/carbon-intensity/forecast")) body = envelope([point(18, null, 77)]);
    else if (url.includes("/regions/")) body = envelope([point(18)]);
    else if (url.includes("/regions")) body = envelope([region(18), region(1, "North Scotland")]);
    else if (url.includes("/carbon-intensity/history")) body = envelope([point(), point(18, 91, 86)]);
    else if (url.includes("/statistics/regional-comparison")) body = envelope([]);
    else body = envelope([]);
    return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("dashboard shell", () => {
  it("loads live data and distinguishes actual values from forecasts", async () => {
    mockApi();
    render(<App />);
    expect(await screen.findByText("Electricity, in context.")).toBeInTheDocument();
    expect(screen.getByText("Estimated actual")).toBeInTheDocument();
    expect(screen.getByText("88", { selector: ".hero-measure strong" })).toBeInTheDocument();
    expect(screen.getByText("Grid intensity over time")).toBeInTheDocument();
  });

  it("shows a recoverable error when the backend cannot be reached", async () => {
    mockApi(true);
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("backend is running");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("opens the regional explorer and lets the user select a region", async () => {
    mockApi();
    render(<App />);
    await screen.findByText("Electricity, in context.");
    fireEvent.click(screen.getByRole("button", { name: "Regional explorer" }));
    expect(await screen.findByText("The grid, region by region.")).toBeInTheDocument();
    const picker = screen.getByLabelText("SELECTED AREA") as HTMLSelectElement;
    fireEvent.change(picker, { target: { value: "1" } });
    await waitFor(() => expect(picker.value).toBe("1"));
  });

  it("opens historical data with date and export controls", async () => {
    mockApi();
    render(<App />);
    await screen.findByText("Electricity, in context.");
    fireEvent.click(screen.getByRole("button", { name: "Historical data" }));
    expect(await screen.findByText("Read the pattern, not just the moment.")).toBeInTheDocument();
    expect(screen.getByLabelText("START DATE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /export csv/i })).toBeInTheDocument();
  });
});
