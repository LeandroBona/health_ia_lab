import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Camera, ChartNoAxesCombined, GitCompareArrows, ListOrdered } from "lucide-react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { VisionHeader, VisionNav, VisionNotice } from "../components/vision/Shared";
import { readSessions } from "../vision/session";
import type { MetricSession } from "../vision/session";

const cards = [
  {title:"Análise de Pose",icon:Camera,description:"Pontos corporais estimados localmente a partir da imagem da webcam."},
  {title:"Ângulos Articulares",icon:Activity,description:"Geometria vetorial sobre ombro, cotovelo e punho ou quadril, joelho e tornozelo."},
  {title:"Comparação entre Lados",icon:GitCompareArrows,description:"Diferença numérica entre os ângulos dos lados anatômicos esquerdo e direito."},
  {title:"Contagem de Movimentos",icon:ListOrdered,description:"Ciclos matemáticos simples ao cruzar dois limites configurados no exemplo."},
  {title:"Histórico de Métricas",icon:ChartNoAxesCombined,description:"Sessões numéricas salvas no navegador somente por escolha explícita."},
];
export function VisionPage(){
  const [sessions,setSessions]=useState<MetricSession[]>([]);
  const [selectedId,setSelectedId]=useState("");
  useEffect(()=>setSessions(readSessions()),[]);
  const selectedSession=sessions.find(session=>session.id===selectedId);
  return <div className="space-y-6"><VisionHeader title="Visão Computacional" subtitle="Estimativa de pose e análise matemática de movimentos utilizando webcam."/><VisionNav/><VisionNotice/>
    <section className="surface-card p-6"><h2 className="section-title">Como a imagem vira métrica</h2><div className="mt-5 flex flex-wrap items-center gap-2 text-sm font-bold">{["CÂMERA","IMAGEM","MODELO DE VISÃO COMPUTACIONAL","LANDMARKS","COORDENADAS","CÁLCULOS","MÉTRICAS DE MOVIMENTO"].map((item,index)=><span className="contents" key={item}>{index>0&&<span aria-hidden="true">→</span>}<span className="rounded-lg bg-sky-50 px-3 py-2 text-sky-900">{item}</span></span>)}</div><p className="mt-4 text-sm text-slate-600">O modelo estima coordenadas de pontos corporais; cálculos geométricos produzem números demonstrativos. Rótulos esquerdo e direito seguem o corpo na imagem, mesmo com a prévia espelhada.</p></section>
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">{cards.map(card=><article className="surface-card p-5" key={card.title}><card.icon className="text-sky-700" size={27}/><h2 className="mt-3 font-bold">{card.title}</h2><p className="mt-2 text-sm text-slate-600">{card.description}</p></article>)}</section>
    <section className="surface-card p-6"><h2 className="section-title">Privacidade e controle</h2><p className="mt-2 text-sm text-slate-600">A câmera só é ativada após clicar no botão. O modelo e seus arquivos são servidos pela própria aplicação; frames e imagens não são enviados ao backend nem armazenados. Apenas ângulos, tempos e contagens são salvos no armazenamento local do navegador quando você escolhe registrar uma sessão.</p><Link className="btn-primary mt-5" to="/visao-computacional/laboratorio">Abrir laboratório</Link></section>
    <section className="surface-card p-6"><h2 className="section-title">Histórico de métricas</h2><p className="mt-2 text-sm text-slate-600">{sessions.length} sessão(ões) numérica(s) salva(s) neste navegador.</p>{sessions.length>0&&<div className="mt-4 overflow-x-auto"><table className="data-table"><thead><tr><th>Data</th><th>Amostras</th><th>Movimentos</th><th>Ângulo médio selecionado</th><th>Ação</th></tr></thead><tbody>{sessions.map(item=><tr key={item.id}><td>{new Date(item.endedAt).toLocaleString("pt-BR")}</td><td>{item.samples.length}</td><td>{item.movements}</td><td>{item.summary[item.selectedJoint]===null?"—":`${item.summary[item.selectedJoint]?.toFixed(1)}°`}</td><td><button className="text-sky-700 underline" onClick={()=>setSelectedId(item.id)}>Ver série</button></td></tr>)}</tbody></table></div>}{selectedSession&&<div className="mt-6"><h3 className="font-bold">Série numérica de {new Date(selectedSession.endedAt).toLocaleString("pt-BR")}</h3><div className="mt-3 h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={selectedSession.samples}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="t" unit=" s"/><YAxis domain={[0,180]} unit="°"/><Tooltip/><Legend/><Line dataKey="leftElbow" name="Cotovelo esquerdo" stroke="#0284c7" dot={false}/><Line dataKey="rightElbow" name="Cotovelo direito" stroke="#e11d48" dot={false}/><Line dataKey="leftKnee" name="Joelho esquerdo" stroke="#7c3aed" dot={false}/><Line dataKey="rightKnee" name="Joelho direito" stroke="#0f766e" dot={false}/></LineChart></ResponsiveContainer></div></div>}</section>
  </div>;
}
