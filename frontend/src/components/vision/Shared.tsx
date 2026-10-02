import { Link } from "react-router-dom";

export const VISION_NOTICE = "Este módulo realiza estimativa computacional de pose para fins educacionais. Os ângulos e métricas apresentados não representam avaliação clínica, diagnóstico ou recomendação fisioterapêutica.";
export function VisionHeader({title,subtitle}:{title:string;subtitle:string}){return <header className="surface-card p-7"><p className="section-kicker">HealthAI Lab · Visão Computacional</p><h1 className="text-3xl font-extrabold text-slate-900">{title}</h1><p className="mt-2 text-slate-600">{subtitle}</p></header>}
export function VisionNotice(){return <p className="rounded-xl border border-sky-200 bg-sky-50 p-4 text-sm font-semibold text-sky-950">{VISION_NOTICE}</p>}
export function VisionNav(){return <nav className="flex flex-wrap gap-2 text-sm font-semibold"><Link className="btn-secondary" to="/visao-computacional">Visão geral</Link><Link className="btn-secondary" to="/visao-computacional/laboratorio">Laboratório de pose</Link></nav>}
