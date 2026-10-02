import { AlertTriangle, BrainCircuit, Database, GraduationCap, HeartHandshake, Layers3 } from "lucide-react";

import { EducationalNotice } from "../components/EducationalNotice";
import { Link } from "react-router-dom";

const pillars = [
  {
    title: "Objetivo educacional",
    description: "Aproximar estudantes dos conceitos de IA por meio de demonstrações progressivas e contextualizadas.",
    icon: GraduationCap,
  },
  {
    title: "Áreas atendidas",
    description: "Fisioterapia, Enfermagem, Farmácia, Medicina Veterinária e Psicologia.",
    icon: HeartHandshake,
  },
  {
    title: "Tipos de IA",
    description: "Aprendizado de máquina, predição, anomalias, linguagem, visão computacional e IA generativa.",
    icon: BrainCircuit,
  },
  {
    title: "Dados sintéticos",
    description: "Exemplos artificiais, criados para aulas e sem representar pessoas ou atendimentos reais.",
    icon: Database,
  },
];

export function AboutPage() {
  return (
    <div className="space-y-7">
      <section className="relative overflow-hidden rounded-3xl bg-ink p-7 text-white sm:p-10">
        <Layers3 className="text-ocean-300" size={38} aria-hidden="true" />
        <p className="mt-7 text-sm font-bold uppercase tracking-[0.18em] text-ocean-300">Sobre o projeto</p>
        <h1 className="mt-2 max-w-3xl text-3xl font-extrabold tracking-tight sm:text-5xl">Tecnologia para aprender, não para diagnosticar.</h1>
        <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-300">
          O HealthAI Lab é um ambiente interdisciplinar para demonstração acadêmica de conceitos de Inteligência
          Artificial aplicados a diferentes áreas da saúde.
        </p>
      </section>

      <section className="surface-card p-6 sm:p-8">
        <h2 className="section-title">Modo Aula</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">Uma apresentação guiada de 15 etapas conecta os módulos existentes a perguntas, comparações e demonstrações reais. As notas do professor ficam ocultas por padrão e a câmera só é ativada mediante comando explícito.</p>
        <Link className="btn-primary mt-5" to="/aula">Preparar apresentação</Link>
      </section>

      <section className="surface-card p-6 sm:p-8">
        <h2 className="section-title">Arquitetura integrada</h2>
        <div className="mt-5 flex flex-wrap items-center gap-2 text-sm font-bold">
          {["FRONTEND", "FASTAPI", "SERVIÇOS", "MODELOS DE IA", "DATABASE / DATASETS"].map((step, index) => <span className="flex items-center gap-2" key={step}>{index > 0 && <span aria-hidden="true">→</span>}<span className="rounded-lg bg-cyan-50 px-3 py-2">{step}</span></span>)}
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          <p className="rounded-xl bg-sky-50 p-4 text-sm"><strong>Visão Computacional:</strong> FRONTEND → POSE ESTIMATION LOCAL. Frames da webcam não são enviados ao backend.</p>
          <p className="rounded-xl bg-fuchsia-50 p-4 text-sm"><strong>IA Generativa:</strong> BACKEND → LLMService → provider externo ou templates locais. Recebe resultados, sem recalcular previsões.</p>
        </div>
        <Link className="btn-secondary mt-5" to="/como-funciona">Comparar técnicas</Link>
      </section>

      <section className="grid gap-4 md:grid-cols-2" aria-label="Pilares do HealthAI Lab">
        {pillars.map(({ title, description, icon: Icon }) => (
          <article key={title} className="surface-card flex gap-4 p-6">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-ocean-50 text-ocean-700">
              <Icon size={23} aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-950">{title}</h2>
              <p className="mt-2 text-base leading-7 text-slate-600">{description}</p>
            </div>
          </article>
        ))}
      </section>

      <section className="surface-card p-6 sm:p-8">
        <div className="flex items-start gap-4">
          <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-amber-50 text-amber-700">
            <AlertTriangle size={23} aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-950">Limitações do sistema</h2>
            <p className="mt-3 text-base leading-7 text-slate-600">
              O conteúdo não substitui formação profissional, avaliação clínica, protocolos institucionais ou
              julgamento de especialistas. Os classificadores de Fisioterapia utilizam exclusivamente relações
              artificiais em dados sintéticos. A visão computacional calcula métricas geométricas e a IA generativa explica saídas estruturadas, sem realizar avaliação clínica.
            </p>
            <p className="mt-4 rounded-xl bg-slate-900 px-5 py-4 text-base font-bold leading-7 text-white">
              O HealthAI Lab foi desenvolvido para demonstração acadêmica de conceitos de Inteligência Artificial e
              não possui finalidade clínica.
            </p>
          </div>
        </div>
      </section>

      <EducationalNotice emphasis />
    </div>
  );
}
