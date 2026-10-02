import { ArrowLeft, Beaker, BookOpen, CheckCircle2, Clock3 } from "lucide-react";
import { Link } from "react-router-dom";

import { EducationalNotice } from "../components/EducationalNotice";
import type { ModuleDefinition } from "../data/modules";

interface ModulePageProps {
  module: ModuleDefinition;
}

export function ModulePage({ module }: ModulePageProps) {
  const Icon = module.icon;

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-2 text-sm font-bold text-ocean-700 hover:text-ocean-900">
        <ArrowLeft size={17} aria-hidden="true" />
        Voltar ao Dashboard
      </Link>

      <section className="surface-card overflow-hidden">
        <div className="grid lg:grid-cols-[1fr_300px]">
          <div className="p-6 sm:p-8 lg:p-10">
            <div className={`grid h-14 w-14 place-items-center rounded-2xl ${module.accent}`}>
              <Icon size={28} aria-hidden="true" />
            </div>
            <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1.5 text-sm font-bold text-amber-800">
              <Clock3 size={16} aria-hidden="true" />
              Planejado para as próximas etapas
            </div>
            <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-slate-950 sm:text-4xl">{module.title}</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-600">{module.description}</p>
          </div>
          <div className="flex flex-col justify-between bg-ink p-6 text-white sm:p-8">
            <Beaker className="text-ocean-300" size={36} aria-hidden="true" />
            <div className="mt-12">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-ocean-300">IA prevista</p>
              <p className="mt-3 text-lg font-bold leading-7 text-white">{module.futureAi}</p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_0.75fr]">
        <section className="surface-card p-6 sm:p-8">
          <div className="flex items-center gap-3">
            <BookOpen className="text-ocean-700" size={22} aria-hidden="true" />
            <h2 className="text-xl font-bold text-slate-950">O que será explorado</h2>
          </div>
          <p className="mt-3 text-base leading-7 text-slate-600">
            Este módulo será implementado nas próximas etapas. A estrutura atual apresenta o escopo acadêmico e
            prepara a navegação para os futuros exercícios práticos.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            {module.concepts.map((concept) => (
              <div key={concept} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <CheckCircle2 className="text-ocean-600" size={19} aria-hidden="true" />
                <p className="mt-3 text-sm font-bold text-slate-800">{concept}</p>
              </div>
            ))}
          </div>
        </section>

        <EducationalNotice emphasis />
      </div>
    </div>
  );
}

