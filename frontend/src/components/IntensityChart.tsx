import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { IntensityPeriod } from "../types";
import { formatNumber, formatRangeTime } from "../utils/format";

interface Props {
  data: IntensityPeriod[];
  height?: number;
  showLegend?: boolean;
}

export function IntensityChart({ data, height = 300, showLegend = true }: Props) {
  if (!data.length) {
    return <div className="empty-chart" role="status">No intensity observations are available for this range.</div>;
  }
  const chartData = [...data].sort((a, b) => Date.parse(a.from) - Date.parse(b.from));
  return (
    <div className="chart-wrap" style={{ height }} aria-label="Carbon intensity history chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 12, left: -14, bottom: 2 }}>
          <CartesianGrid stroke="#e8ede8" strokeDasharray="3 4" vertical={false} />
          <XAxis dataKey="from" tickFormatter={formatRangeTime} tickLine={false} axisLine={false} minTickGap={32} />
          <YAxis width={52} tickLine={false} axisLine={false} tickFormatter={(value: number) => String(value)} />
          <Tooltip
            labelFormatter={(value) => formatRangeTime(String(value))}
            formatter={(value) => [`${formatNumber(Number(value))} gCO₂/kWh`, ""]}
            contentStyle={{ borderRadius: 12, borderColor: "#dfe7df", boxShadow: "0 8px 24px #18351b12" }}
          />
          {showLegend && <Legend verticalAlign="top" height={34} iconType="circle" />}
          <Line name="Estimated actual" type="monotone" dataKey="actual" stroke="#122b21" strokeWidth={2.4} dot={false} connectNulls={false} />
          <Line name="Forecast" type="monotone" dataKey="forecast" stroke="#16a36a" strokeWidth={2.4} strokeDasharray="5 4" dot={false} connectNulls={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
