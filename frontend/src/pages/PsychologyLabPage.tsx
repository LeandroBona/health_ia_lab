import { useState } from "react";
import { AnalysisView, PsychologyHeader, PsychologyNav, PsychologyNotice, examples } from "../components/psychology/Shared";
import { psychologyApi } from "../services/api";
import type { PsychologyAnalysis } from "../types/psychology";

export function PsychologyLabPage() {
  const [text, setText] = useState("");
  const [analysis, setAnalysis] = useState<PsychologyAnalysis | null>(null);
  const [showProcessing, setShowProcessing] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function analyze() {
    if (!text.trim()) { setError("Digite um relato fictício antes de analisar."); setAnalysis(null); return; }
    setBusy(true); setError(""); setAnalysis(null);
    try { setAnalysis(await psychologyApi.analyze(text)); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  return <div className="space-y-6"><PsychologyHeader title="Laboratório de Processamento de Linguagem Natural" subtitle="Explore como um texto fictício se transforma em números, temas e relações matemáticas."/><PsychologyNav/><PsychologyNotice/>
    <section className="surface-card p-6"><h2 className="section-title">Fluxo de análise</h2><div className="mt-4 flex flex-wrap items-center gap-2 text-sm font-bold">{["TEXTO","TOKENIZAÇÃO","TF-IDF","MODELO","RESULTADO"].map((step,index)=><span className="contents" key={step}>{index>0&&<span aria-hidden="true">→</span>}<span className="rounded-lg bg-rose-50 px-3 py-2 text-rose-900">{step}</span></span>)}</div><p className="mt-3 text-sm text-slate-600">O computador não compreende um relato como uma pessoa. O TF-IDF representa termos como números para que os modelos encontrem padrões.</p></section>
    <section className="surface-card p-6"><label className="font-bold" htmlFor="psychology-text">Relato fictício</label><textarea id="psychology-text" className="field mt-3 min-h-44 w-full" placeholder="Digite ou cole aqui um relato fictício para análise..." value={text} onChange={e=>setText(e.target.value)}/><div className="mt-4 flex flex-wrap gap-2"><span className="self-center text-sm font-semibold">Carregar exemplo:</span>{examples.map(item=><button className="btn-secondary" key={item.label} onClick={()=>{setText(item.text);setAnalysis(null);setError("")}}>{item.label}</button>)}</div><div className="mt-5 flex flex-wrap items-center gap-4"><button className="btn-primary" disabled={busy} onClick={analyze}>{busy?"Analisando...":"Analisar texto"}</button><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={showProcessing} onChange={e=>setShowProcessing(e.target.checked)}/>Mostrar processamento</label></div>{error&&<p className="mt-4 text-rose-700" role="alert">{error}</p>}</section>
    {analysis&&<section className="surface-card p-6"><h2 className="section-title">Resultado da análise linguística</h2><div className="mt-5"><AnalysisView analysis={analysis} showProcessing={showProcessing}/></div></section>}
  </div>;
}
