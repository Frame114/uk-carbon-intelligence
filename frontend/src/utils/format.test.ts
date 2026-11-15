import { describe, expect, it } from "vitest";
import { formatNumber, londonDateToUtc } from "./format";

describe("presentation helpers", () => {
  it("does not turn missing or zero values into misleading output", () => {
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(0)).toBe("0");
  });

  it("converts London local dates to UTC across daylight saving offsets", () => {
    expect(londonDateToUtc("2026-01-15").toISOString()).toBe("2026-01-15T00:00:00.000Z");
    expect(londonDateToUtc("2026-07-15").toISOString()).toBe("2026-07-14T23:00:00.000Z");
  });
});
