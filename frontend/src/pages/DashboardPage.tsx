import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, BarChart3, Bot, Camera, Database, FileSpreadsheet, FileText, History, Layers3, Sparkles, Users } from "lucide-react";
import { EducationalNotice } from "../components/EducationalNotice";
import { MetricCard } from "../components/MetricCard";
import { PageHeader, StatusBadge, moduleLabels } from "../components/platform/Shared";
import { api, platformApi } from "../services/api";
import { readSessions } from "../vision/session";
import type { CatalogModel } from "../types/platform";

const areas=[
  {module:"fisioterapia",data:"Dados estruturados",ai:"Classificação supervisionada",model:"Random Forest / Logistic Regression"},
  {module:"enfermagem",data:"Sinais temporais",ai:"Detecção de anomalias",model:"Isolation Forest"},
  {module:"farmacia",data:"Dados estruturados e séries temporais",ai:"Classificação + regressão",model:"Classificador / regressão"},
  {module:"veterinaria",data:"Animais e acompanhamentos sintéticos",ai:"Classificação + anomalias",model:"Classificador / Isolation Forest"},
  {module:"psicologia",data:"Relatos sintéticos",ai:"NLP + clustering + similaridade",model:"TF-IDF / Logistic Regression / KMeans"},
];
const techniques=["Classificação","Regressão","Detecção de Anomalias","Clustering","NLP","Visão Computacional","IA Generativa"];
const dataKinds=[
  {name:"Planilha",icon:FileSpreadsheet,uses:"Fisioterapia · Farmácia · Veterinária",to:"/datasets"},
  {name:"Série temporal",icon:BarChart3,uses:"Enfermagem · Farmácia · Veterinária",to:"/datasets"},
  {name:"Texto",icon:FileText,uses:"Psicologia · IA Generativa",to:"/psicologia"},
  {name:"Imagem / Vídeo",icon:Camera,uses:"Visão Computacional",to:"/visao-computacional"},
  {name:"Prompt",icon:Sparkles,uses:"IA Generativa",to:"/ia-generativa"},
];
const limits=["Dados podem conter vieses","Modelos podem errar","Probabilidade não é certeza","Correlação não é causalidade","IA generativa pode produzir informações incorretas","Resultados precisam de interpretação humana"];
export function DashboardPage(){
  const [summary,setSummary]=useState({datasets:0,models:0,analyses:0,patients:0}),[models,setModels]=useState<CatalogModel[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(false);
  const [sessions,setSessions]=useState(0);
  useEffect(()=>{setSessions(readSessions().length);Promise.allSettled([api.getDashboard(),platformApi.models(),platformApi.datasets(),platformApi.history(new URLSearchParams({page_size:"1"}))]).then(([dashboard,modelResult,datasetResult,historyResult])=>{
    if(dashboard.status==="fulfilled")setSummary(current=>({...current,patients:dashboard.value.patients}));
    if(modelResult.status==="fulfilled"){setModels(modelResult.value.items);setSummary(current=>({...current,models:modelResult.value.items.length}))}
    if(datasetResult.status==="fulfilled")setSummary(current=>({...current,datasets:datasetResult.value.items.length}));
    if(historyResult.status==="fulfilled")setSummary(current=>({...current,analyses:historyResult.value.total}));
    setError([dashboard,modelResult,datasetResult,historyResult].some(result=>result.status==="rejected"));setLoading(false);
  })},[]);
  return <div className="space-y-9"><PageHeader title="HealthAI Lab" subtitle="Laboratório Educacional de Inteligência Artificial aplicada à Saúde" actions={<div className="flex flex-wrap gap-2"><Link className="btn-primary" to="/aula">Iniciar Modo Aula</Link><Link className="btn-secondary" to="/laboratorio">Abrir Laboratório Geral</Link><Link className="btn-secondary" to="/como-funciona">Como funciona</Link></div>}/>{error&&<p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-950">Alguns indicadores ainda não puderam ser atualizados.</p>}
    <section><h2 className="section-title">Visão consolidada</h2><div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{[
      {label:"Datasets disponíveis",value:summary.datasets,icon:Database,helper:"Conjuntos sintéticos catalogados"},
      {label:"Modelos de IA",value:summary.models,icon:Bot,helper:"Inclui visão local e explicação textual"},
      {label:"Áreas da saúde",value:5,icon:Users,helper:"Fisioterapia, Enfermagem, Farmácia, Veterinária e Psicologia"},
      {label:"Tipos de IA",value:7,icon:Layers3,helper:"Técnicas demonstradas"},
      {label:"Análises executadas",value:summary.analyses,icon:History,helper:"Eventos educacionais registrados"},
      {label:"Sessões de visão computacional",value:sessions,icon:Camera,helper:"Métricas salvas neste navegador"},
    ].map(card=><MetricCard key={card.label} {...card} tone="bg-cyan-50 text-cyan-700" loading={loading}/>)}</div></section>
    <section><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="section-kicker">Áreas disponíveis</p><h2 className="section-title">Escolha um módulo</h2></div><Link className="text-sm font-bold text-cyan-700 underline" to="/laboratorio">Ver todos os experimentos</Link></div><div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{areas.map(area=>{const entries=models.filter(item=>item.module===area.module);const ready=entries.some(item=>item.status==="ready");return <Link to={`/${area.module}`} key={area.module} className="surface-card block p-6 transition-transform hover:-translate-y-0.5"><div className="flex justify-between gap-3"><h3 className="text-xl font-bold">{moduleLabels[area.module]}</h3><StatusBadge status={ready?"ready":"unavailable"}/></div><dl className="mt-4 space-y-2 text-sm"><div><dt className="text-slate-500">Tipo de dado</dt><dd className="font-semibold">{area.data}</dd></div><div><dt className="text-slate-500">Tipo de IA</dt><dd className="font-semibold">{area.ai}</dd></div><div><dt className="text-slate-500">Modelo principal</dt><dd className="font-semibold">{area.model}</dd></div></dl></Link>})}</div></section>
    <section className="surface-card p-6"><h2 className="section-title">Tipos de Inteligência Artificial utilizados</h2><p className="mt-2 text-sm text-slate-600">Abra um tipo para conhecer sua entrada, saída e módulos de aplicação.</p><div className="mt-4 flex flex-wrap gap-2">{techniques.map(item=><Link key={item} className="rounded-xl border border-cyan-200 bg-cyan-50 px-4 py-3 text-sm font-bold text-cyan-900 hover:bg-cyan-100" to="/como-funciona">{item} →</Link>)}</div></section>
    <section><h2 className="section-title">Explore por tipo de dado</h2><div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-5">{dataKinds.map(item=><Link className="surface-card p-5" to={item.to} key={item.name}><item.icon className="text-cyan-700" size={28}/><h3 className="mt-3 font-bold uppercase">{item.name}</h3><p className="mt-2 text-sm text-slate-600">{item.uses}</p></Link>)}</div></section>
    <section className="surface-card p-6"><h2 className="section-title">Da informação à Inteligência Artificial</h2><div className="mt-4 flex flex-wrap gap-2">{["Dado","Preparação","Modelo","Resultado","Explicação","Decisão humana"].map((step,index)=><span key={step} className="flex items-center gap-2 text-sm font-bold">{index>0&&<span aria-hidden="true">→</span>}<span className={`rounded-lg px-3 py-2 ${index===5?"bg-emerald-100 text-emerald-900":"bg-slate-100"}`}>{step}</span></span>)}</div><p className="mt-4 text-sm text-slate-600">O resultado estatístico e a explicação textual apoiam uma interpretação técnica; a etapa final pertence a pessoas.</p></section>
    <section><h2 className="section-title">IA não é infalível</h2><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{limits.map(item=><p className="surface-card flex items-center gap-3 p-4 text-sm font-semibold" key={item}><Activity size={17} className="text-amber-700"/>{item}</p>)}</div></section><EducationalNotice/></div>
}
