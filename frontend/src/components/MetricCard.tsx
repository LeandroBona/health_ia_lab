import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: number | string;
  helper: string;
  icon: LucideIcon;
  tone?: string;
  loading?: boolean;
  valueClassName?: string;
}

export function MetricCard({ label, value, helper, icon: Icon, tone = "bg-cyan-50 text-cyan-700", loading = false, valueClassName = "text-4xl" }: MetricCardProps) {
  return (
    <article className="surface-card relative overflow-hidden p-5 sm:p-6">
      <div className="absolute -right-8 -top-8 h-28 w-28 rounded-full bg-slate-100/70" aria-hidden="true" />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold leading-5 text-slate-500">{label}</p>
          {loading ? (
            <div className="mt-3 h-10 w-20 animate-pulse rounded-lg bg-slate-100" aria-label="Carregando" />
          ) : (
            <p className={`mt-2 font-extrabold tracking-tight text-slate-950 ${valueClassName}`}>{value}</p>
          )}
          <p className="mt-2 text-sm text-slate-500">{helper}</p>
        </div>
        <div className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl ${tone}`}>
          <Icon size={24} aria-hidden="true" />
        </div>
      </div>
    </article>
  );
}
