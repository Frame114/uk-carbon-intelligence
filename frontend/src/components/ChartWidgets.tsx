import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ComparisonSummary } from "../types";
import { formatLocalTime, formatNumber } from "../utils/format";

const MIX_COLORS = ["#1b8a61", "#9ecb74", "#c7a858", "#557a91", "#6b9bc0", "#93b7a5", "#b5a585", "#77876f", "#b5c5bd"];

export function GenerationMixChart({
  data,
  periodStart,
}: {
  data: Array<{ fuel: string; perc: number }>;
  periodStart?: string;
}) {
  return (
    <div className="mix-content">
      <div className="mix-donut">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="perc" nameKey="fuel" innerRadius="67%" outerRadius="94%" paddingAngle={1} stroke="none">
              {data.map((item, index) => <Cell key={item.fuel} fill={MIX_COLORS[index % MIX_COLORS.length]} />)}
            </Pie>
            <Tooltip formatter={(value) => [`${value}%`, "Share"]} />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center"><strong>{periodStart ? formatLocalTime(periodStart, { hour: "2-digit", minute: "2-digit" }) : "—"}</strong><span>period start</span></div>
      </div>
      <div className="mix-legend">
        {data.slice(0, 6).map((item, index) => (
          <div key={item.fuel}><i style={{ background: MIX_COLORS[index % MIX_COLORS.length] }} /><span>{item.fuel}</span><strong>{item.perc}%</strong></div>
        ))}
      </div>
    </div>
  );
}

export function RegionalComparisonChart({ data }: { data: ComparisonSummary[] }) {
  return (
    <div className="comparison-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: -15, right: 10, top: 12, bottom: 0 }}>
          <CartesianGrid stroke="#e8ede8" vertical={false} strokeDasharray="3 4" />
          <XAxis dataKey="region_name" tickLine={false} axisLine={false} interval={0} tick={{ fontSize: 11 }} />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => [`${formatNumber(Number(value))} gCO₂/kWh`, ""]} />
          <Bar dataKey="average" name="Period average" fill="#1c8b63" radius={[5, 5, 0, 0]} maxBarSize={54} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
