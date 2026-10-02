import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Distribution, PhysioStats } from "../../types/physiotherapy";
import { resultLabels } from "./shared";

export function DistributionChart({
  title,
  data,
  horizontal = false,
  description,
}: {
  title: string;
  data: Distribution[];
  horizontal?: boolean;
  description?: string;
}) {
  return (
    <section className="surface-card min-w-0 p-5 sm:p-6">
      <h2 className="text-lg font-bold">{title}</h2>
      {description && (
        <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>
      )}
      <div
        className="mt-5 w-full"
        style={{ height: horizontal ? Math.max(220, data.length * 34) : 250 }}
        role="img"
        aria-label={`${title}: ${data.map((item) => `${item.name}: ${item.count}`).join(", ")}`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout={horizontal ? "vertical" : "horizontal"}
            margin={{ left: horizontal ? 10 : -15, right: 20, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="4 4"
              horizontal={!horizontal}
              vertical={horizontal}
              stroke="#e2e8f0"
            />
            {horizontal ? (
              <>
                <XAxis
                  type="number"
                  allowDecimals={false}
                  tick={{ fontSize: 14 }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={155}
                  tick={{ fontSize: 14, fill: "#475569" }}
                  interval={0}
                />
              </>
            ) : (
              <>
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 14, fill: "#475569" }}
                />
                <YAxis allowDecimals={false} tick={{ fontSize: 14 }} />
              </>
            )}
            <Tooltip
              formatter={(value) => [value, "Quantidade"]}
              cursor={{ fill: "#f1f5f9" }}
            />
            <Bar
              dataKey="count"
              fill="#118589"
              radius={horizontal ? [0, 5, 5, 0] : [5, 5, 0, 0]}
              maxBarSize={42}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
export function PhysioCharts({ stats }: { stats: PhysioStats }) {
  return (
    <div className="grid min-w-0 gap-5 xl:grid-cols-2">
      <DistributionChart
        title="Distribuição dos resultados"
        horizontal
        data={(Object.keys(resultLabels) as (keyof typeof resultLabels)[]).map(
          (key) => ({ name: resultLabels[key], count: stats.results[key] }),
        )}
        description="Rótulos artificiais registrados no dataset."
      />
      <section className="surface-card min-w-0 p-6">
        <h2 className="text-lg font-bold">Dor inicial × dor atual</h2>
        <p className="mt-1 text-sm text-slate-500">
          Médias registradas · escala de 0 a 10
        </p>
        <div
          className="mt-5 h-[250px]"
          role="img"
          aria-label={`Dor média inicial ${stats.average_pain_initial}; atual ${stats.average_pain_current}`}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={[
                { name: "Inicial", value: stats.average_pain_initial },
                { name: "Atual", value: stats.average_pain_current },
              ]}
            >
              <CartesianGrid strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 14 }} />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Bar
                dataKey="value"
                name="Dor média"
                fill="#507aab"
                radius={[6, 6, 0, 0]}
                maxBarSize={75}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
      <DistributionChart
        title="Adesão aos exercícios"
        description="Pacientes por faixa de adesão registrada."
        data={stats.adherence_distribution}
      />
      <DistributionChart
        title="Tipos de lesão"
        horizontal
        data={stats.injuries}
      />
    </div>
  );
}
