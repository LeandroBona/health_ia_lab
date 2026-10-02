import { useEffect, useState } from "react";
import { PsychologyHeader, PsychologyNav, PsychologyNotice } from "../components/psychology/Shared";
import { psychologyApi } from "../services/api";
import type { PsychologyCluster, PsychologyModel } from "../types/psychology";

export function PsychologyModelPage() {
  const [model,setModel]=useState<PsychologyModel|null>(null);
  const [groups,setGroups]=useState<PsychologyCluster[]>([]);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  useEffect(()=>{psychologyApi.model().then(setModel).catch(e=>setError(String(e)));psychologyApi.clusters().then(data=>setGroups(data.groups)).catch(e=>setError(String(e)))},[]);
  async function train(){setBusy(true);setError("");try{setModel(await psychologyApi.train());setGroups((await psychologyApi.clusters()).groups)}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
  const metricLabels:Record<string,string>={accuracy:"Accuracy",precision_macro:"Precision Macro",recall_macro:"Recall Macro",f1_macro:"F1 Macro"};
  return <div className="space-y-6"><PsychologyHeader title="Modelos NLP e métricas" subtitle="Classificação temática, agrupamento e similaridade de relatos sintéticos."/><PsychologyNav/><PsychologyNotice/>{error&&<p className="text-rose-700">{error}</p>}
    <section className="surface-card p-6"><div className="flex flex-wrap justify-between gap-4"><div><h2 className="section-title">Classificação temática</h2><p className="mt-2 text-sm text-slate-600">TF-IDF → Logistic Regression · texto como entrada; tema principal sintético como rótulo.</p></div><button className="btn-primary" disabled={busy} onClick={train}>{busy?"Treinando...":"Treinar novamente"}</button></div>{model&&<><div className="mt-5 grid gap-3 md:grid-cols-4">{Object.entries(metricLabels).map(([key,label])=><div className="rounded-lg bg-rose-50 p-4" key={key}><p className="text-sm">{label}</p><strong className="text-xl">{model.metrics[key]?.toFixed(3)??"—"}</strong></div>)}</div><dl className="mt-5 grid gap-2 text-sm md:grid-cols-3"><div>Algoritmo: <strong>{model.algorithm}</strong></div><div>Status: <strong>{model.status}</strong></div><div>Versão: <strong>{model.version}</strong></div><div>Treino: <strong>{model.train_records}</strong></div><div>Teste: <strong>{model.test_records}</strong></div><div>Características TF-IDF: <strong>{model.features}</strong></div></dl><p className="mt-3 text-sm text-slate-600">{model.evaluation_note}</p></>}</section>
    {model&&<section className="surface-card p-6"><h2 className="section-title">Matriz de confusão</h2><p className="mt-2 text-sm text-slate-600">Linhas: tema registrado · colunas: tema previsto no conjunto de teste.</p><div className="mt-4 overflow-x-auto"><table className="data-table"><thead><tr><th>Registrado ↓ / Previsto →</th>{model.labels.map(label=><th key={label}>{label}</th>)}</tr></thead><tbody>{model.confusion_matrix.map((row,i)=><tr key={model.labels[i]}><th>{model.labels[i]}</th>{row.map((value,j)=><td key={j}>{value}</td>)}</tr>)}</tbody></table></div></section>}
    <section className="surface-card p-6"><h2 className="section-title">Agrupamento de textos</h2><p className="mt-2 text-sm">TF-IDF + KMeans · {model?.cluster_count??5} grupos. O algoritmo não recebeu os temas antes e agrupou vetores matematicamente próximos.</p><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">{groups.map(group=><div className="rounded-xl bg-violet-50 p-4" key={group.cluster_id}><strong>{group.label}</strong><p className="text-sm">{group.quantidade} relatos</p><p className="mt-2 text-xs">{group.top_terms.join(", ")}</p></div>)}</div></section>
    <section className="surface-card p-6"><h2 className="section-title">Similaridade textual</h2><p className="mt-2 text-sm">TF-IDF + similaridade de cosseno · compara vetores e retorna os cinco relatos mais próximos. Proximidade matemática não implica experiência pessoal semelhante.</p></section>
  </div>;
}
