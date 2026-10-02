import type { LucideIcon } from "lucide-react";

interface AITypeCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  index: number;
}

export function AITypeCard({ title, description, icon: Icon, index }: AITypeCardProps) {
  return (
    <article className="surface-card flex gap-4 p-5">
      <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-slate-900 text-ocean-300">
        <Icon size={21} aria-hidden="true" />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-extrabold text-slate-300">0{index + 1}</span>
          <h3 className="font-bold text-slate-950">{title}</h3>
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
      </div>
    </article>
  );
}

