import { Link } from "react-router-dom";
import type { ReactNode } from "react";

export const nursingNotice = "Todos os registros são sintéticos e utilizados exclusivamente para demonstração acadêmica. Nenhuma classificação representa diagnóstico, risco ou gravidade.";
export function NursingHeader({title, subtitle, children}: {title:string;subtitle:string;children?:ReactNode}) {
  return <header className="surface-card p-6 sm:p-8"><p className="section-kicker">HealthAI Lab · Enfermagem</p><div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">{title}</h1><p className="mt-2 max-w-3xl text-base text-slate-600 sm:text-lg">{subtitle}</p></div><div className="flex flex-wrap gap-2">{children}</div></div><p className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm font-medium leading-6 text-amber-900">{nursingNotice}</p></header>;
}
export function NursingNav() { return <nav className="flex flex-wrap gap-2" aria-label="Navegação de Enfermagem"><Link className="btn-secondary" to="/enfermagem">Visão geral</Link><Link className="btn-secondary" to="/enfermagem/modelo">Modelo</Link><Link className="btn-secondary" to="/enfermagem/laboratorio">Laboratório</Link><Link className="btn-secondary" to="/enfermagem/dataset">Dataset</Link><Link className="btn-secondary" to="/enfermagem/dataset/temporal">Série temporal</Link><Link className="btn-secondary" to="/enfermagem/importar">Importar</Link></nav>; }
export function StatusBadge({classification}: {classification:string|null}) { return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${classification === "anomalia" ? "bg-amber-100 text-amber-900" : "bg-teal-100 text-teal-900"}`}>{classification === "anomalia" ? "Anomalia" : classification === "padrao" ? "Padrão" : "Não analisado"}</span>; }
export function NursingLoading() { return <div className="surface-card p-8 text-slate-600" role="status">Carregando dados sintéticos...</div>; }
export function NursingError({message}: {message:string}) { return <div className="surface-card border-rose-200 p-6 text-rose-800" role="alert">{message}</div>; }
export const formatDate = (value:string) => new Date(value).toLocaleString("pt-BR", {dateStyle:"short",timeStyle:"short"});
