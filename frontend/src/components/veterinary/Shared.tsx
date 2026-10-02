import { Link } from "react-router-dom";
import type { Evolution, VetPrediction } from "../../types/veterinary";

export const labels: Record<Evolution,string> = {
  evolucao_esperada:"Evolução esperada no dataset",
  acompanhamento_adicional:"Acompanhamento adicional no dataset",
  dados_insuficientes:"Dados insuficientes",
};
export const notice = "Os dados e resultados apresentados neste módulo são sintéticos e possuem finalidade exclusivamente educacional.";
export const categories = Object.keys(labels) as Evolution[];

export function VetHeader({title,subtitle}:{title:string;subtitle:string}) {return <header className="surface-card p-7"><p className="section-kicker">HealthAI Lab · Veterinária</p><h1 className="text-3xl font-extrabold text-slate-900">{title}</h1><p className="mt-2 text-slate-600">{subtitle}</p></header>}
export function VetNav(){return <nav className="flex flex-wrap gap-2 text-sm font-semibold"><Link className="btn-secondary" to="/veterinaria">Animais</Link><Link className="btn-secondary" to="/veterinaria/laboratorio">Laboratório</Link><Link className="btn-secondary" to="/veterinaria/modelo">Modelos e métricas</Link><Link className="btn-secondary" to="/veterinaria/importar">Datasets</Link></nav>}
export function VetNotice(){return <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm font-medium text-amber-950">{notice}</p>}
export function Indicator({label,value}:{label:string;value:number}){return <div><div className="mb-1 flex justify-between text-sm"><span>{label}</span><strong>{value.toFixed(1)}%</strong></div><div className="h-3 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-cyan-600" style={{width:`${Math.max(0,Math.min(100,value))}%`}}/></div></div>}
export function PredictionView({result}:{result:VetPrediction}){return <div className="space-y-4"><p className="text-lg font-bold">Classificação: {labels[result.prediction]}</p>{categories.map(category=><Indicator key={category} label={labels[category]} value={(result.probabilities[category]??0)*100}/>)}{result.actual_result&&<p className="text-sm">Resultado registrado: <strong>{labels[result.actual_result]}</strong>. O modelo {result.correct?"acertou a categoria registrada":"classificou diferente do resultado registrado"}.</p>}<p className="text-sm text-slate-600">Uma previsão probabilística não representa certeza ou avaliação veterinária.</p></div>}
