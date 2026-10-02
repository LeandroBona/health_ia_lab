import { Activity, Sparkles } from "lucide-react";

export function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="relative grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-ocean-400 text-ink shadow-lg shadow-ocean-900/20">
        <Activity aria-hidden="true" size={23} strokeWidth={2.5} />
        <Sparkles
          aria-hidden="true"
          className="absolute -right-1 -top-1 rounded-full bg-white p-0.5 text-ocean-700"
          size={14}
        />
      </div>
      <div>
        <p className="text-lg font-extrabold tracking-tight text-white">HealthAI Lab</p>
        <p className="text-xs font-medium tracking-wide text-slate-400">IA PARA SAÚDE</p>
      </div>
    </div>
  );
}

