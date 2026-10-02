import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { applicationChartData } from "../data/modules";

interface TooltipPayload {
  value?: number;
  payload?: { area?: string };
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

function ChartTooltip({ active, payload }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;

  const item = payload[0];
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-lg">
      <p className="text-sm font-bold text-slate-900">{item.payload?.area}</p>
      <p className="text-xs text-slate-500">{item.value} abordagens previstas</p>
    </div>
  );
}

export function ApplicationMapChart() {
  return (
    <div className="surface-card p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-bold text-ocean-700">MAPA CONCEITUAL</p>
          <h3 className="mt-1 text-lg font-bold text-slate-950">Abordagens previstas por área</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">Dados do escopo</span>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        Quantidade de técnicas de IA indicadas para cada trilha futura.
      </p>
      <div className="mt-5 h-64 w-full" aria-label="Gráfico de abordagens de IA previstas por área">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={applicationChartData} margin={{ top: 8, right: 4, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="area" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: "#f1f5f9" }} />
            <Bar dataKey="abordagens" fill="#18a6a6" radius={[7, 7, 0, 0]} maxBarSize={48} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

