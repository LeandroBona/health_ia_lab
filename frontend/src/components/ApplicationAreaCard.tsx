import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

import type { ModuleDefinition } from "../data/modules";

interface ApplicationAreaCardProps {
  module: ModuleDefinition;
}

export function ApplicationAreaCard({ module }: ApplicationAreaCardProps) {
  const Icon = module.icon;

  return (
    <Link
      to={`/${module.path}`}
      className="surface-card group flex min-h-56 flex-col p-5 transition duration-200 hover:-translate-y-1 hover:border-ocean-200 hover:shadow-lg"
    >
      <div className="flex items-start justify-between gap-3">
        <div className={`grid h-12 w-12 place-items-center rounded-2xl ${module.accent}`}>
          <Icon size={24} aria-hidden="true" />
        </div>
        <ArrowUpRight
          className="text-slate-300 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-ocean-600"
          size={20}
          aria-hidden="true"
        />
      </div>
      <h3 className="mt-5 text-lg font-bold text-slate-950">{module.title}</h3>
      <p className="mt-2 flex-1 text-sm leading-6 text-slate-600">{module.shortDescription}</p>
      <p className="mt-4 border-t border-slate-100 pt-4 text-sm font-semibold leading-5 text-ocean-700">
        {module.futureAi}.
      </p>
    </Link>
  );
}

