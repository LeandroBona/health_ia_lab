import { Link } from "react-router-dom";
import { PageHeader } from "../components/platform/Shared";

const experiments=[
  {area:"Fisioterapia",name:"Classificação de evolução",input:"Dados estruturados",model:"Random Forest ou Logistic Regression",output:"Categoria e probabilidades",to:"/fisioterapia/laboratorio",button:"Abrir Laboratório de Previsão"},
  {area:"Enfermagem",name:"Detecção de anomalias",input:"Sinais numéricos",model:"Isolation Forest",output:"Padrão / anomalia",to:"/enfermagem/laboratorio"},
  {area:"Farmácia",name:"Classificação de adesão",input:"Dados estruturados",model:"Classificador supervisionado",output:"Categoria e probabilidades",to:"/farmacia/adesao/laboratorio"},
  {area:"Farmácia",name:"Previsão de demanda",input:"Série temporal",model:"Regressão",output:"Demanda estimada",to:"/farmacia/demanda/laboratorio"},
  {area:"Veterinária",name:"Classificação e anomalias",input:"Animal fictício e acompanhamentos",model:"Classificador + Isolation Forest",output:"Categoria / registro diferente",to:"/veterinaria/laboratorio"},
  {area:"Psicologia",name:"Análise de texto",input:"Relato fictício",model:"TF-IDF + Logistic Regression + KMeans",output:"Palavras-chave, tema, similaridade e grupo",to:"/psicologia/laboratorio"},
  {area:"Visão Computacional",name:"Análise de movimento",input:"Webcam local",model:"MediaPipe Pose Landmarker",output:"Landmarks, ângulos e movimentos",to:"/visao-computacional/laboratorio"},
  {area:"IA Generativa",name:"Construtor de prompts",input:"Prompt e contexto",model:"LLM opcional / templates locais",output:"Texto educacional",to:"/ia-generativa"},
];
const journey=[
  ["Prever um paciente fictício","/fisioterapia/pacientes/PAC-0001"],
  ["Alterar variáveis no simulador","/fisioterapia/simulador?patientId=PAC-0001"],
  ["Encontrar uma anomalia","/enfermagem"],
  ["Prever demanda","/farmacia/demanda"],
  ["Analisar um texto","/psicologia/laboratorio"],
  ["Identificar movimento pela webcam","/visao-computacional/laboratorio"],
  ["Pedir explicação à IA Generativa","/ia-generativa"],
];
export function GeneralLabPage(){return <div className="space-y-7"><PageHeader title="Laboratório Geral de IA" subtitle="Escolha a entrada e o modelo que deseja experimentar. Cada laboratório mantém a análise no seu módulo especializado."/><section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{experiments.map(item=><article className="surface-card flex flex-col p-6" key={item.name}><p className="section-kicker">{item.area}</p><h2 className="mt-2 text-xl font-bold">{item.name}</h2><dl className="mt-4 space-y-2 text-sm"><div><dt className="font-bold">Entrada</dt><dd>{item.input}</dd></div><div><dt className="font-bold">Modelo</dt><dd>{item.model}</dd></div><div><dt className="font-bold">Saída</dt><dd>{item.output}</dd></div></dl><Link className="btn-primary mt-auto self-start pt-2" to={item.to}>{item.button??"Experimentar"}</Link></article>)}</section><section className="surface-card p-6"><h2 className="section-title">Experimentos recomendados para demonstração</h2><ol className="mt-4 grid gap-3 md:grid-cols-2">{journey.map(([label,to],index)=><li key={label}><Link className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 hover:bg-slate-50" to={to}><span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-cyan-100 text-sm font-bold text-cyan-900">{index+1}</span><span className="font-semibold">{label}</span></Link></li>)}</ol><p className="mt-4 text-sm text-slate-600">Esta é uma sugestão de exploração livre; não inicia o Modo Aula.</p></section></div>}
