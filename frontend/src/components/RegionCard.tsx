import { ArrowDownRight, ArrowUpRight, MapPin } from "lucide-react";
import type { RegionSnapshot } from "../types";
import { formatNumber } from "../utils/format";

interface Props {
  region: RegionSnapshot;
  onSelect: (id: number) => void;
}

export function RegionCard({ region, onSelect }: Props) {
  const value = region.current?.forecast;
  const trend = region.current?.forecast_classification;
  const isLow = trend === "very low" || trend === "low";
  return (
    <button className="region-card" onClick={() => onSelect(region.id)} disabled={!region.available}>
      <span className="region-card-top"><span className="region-pin"><MapPin size={14} /></span><span className="region-kind">{region.type === "country" ? "Country aggregate" : region.type === "national" ? "GB aggregate" : "DNO region"}</span></span>
      <span className="region-title">{region.name}</span>
      <span className="region-value">{region.available ? formatNumber(value) : "No data"}<small>{region.available ? "gCO₂/kWh" : "currently unavailable"}</small></span>
      {region.available && <span className={`region-trend ${isLow ? "is-clean" : ""}`}>{isLow ? <ArrowDownRight size={15} /> : <ArrowUpRight size={15} />}{trend ?? "Forecast"}</span>}
    </button>
  );
}
