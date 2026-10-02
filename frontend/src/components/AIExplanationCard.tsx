import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { generativeApi } from "../services/api";
import { addHistory } from "../services/generativeHistory";
import type { AnalysisType, ExplainInput, ExplanationLevel, GeneratedText, GenerativeModule } from "../types/generative";

interface Props { title: string; sourceData: Record<string, unknown>; module: GenerativeModule; analysisType: AnalysisType; recordReference?:string }

export function AIExplanationCard({title,sourceData,module,analysisType,recordReference}:Props) {
  const [level,setLevel]=useState<ExplanationLevel>("Simples");
  const [result,setResult]=useState<GeneratedText|null>(null);
  const [state,setState]=useState<"idle"|"loading"|"done"|"error">("idle");
  const [error,setError]=useState("");
  const sourceKey=JSON.stringify(sourceData);
  useEffect(()=>{setResult(null);setState("idle");setError("")},[sourceKey]);
  async function generate(provider: "auto"|"local"="auto") {
    setState("loading"); setError("");
    const input:ExplainInput={module,analysis_type:analysisType,data:sourceData,level,provider,record_reference:recordReference};
    try {
      const answer=await generativeApi.explain(input);
      setResult(answer); setState("done");
      addHistory({module,analysisType,provider:answer.provider,generatedAt:answer.generated_at});
    } catch (cause) {
      setError(cause instanceof Error?cause.message:"Não foi possível gerar a explicação externa."); setState("error");
    }
  }
  return <section className="surface-card p-6" aria-label={title}>
    <div className="flex items-center gap-3"><Sparkles className="text-fuchsia-700" size={23}/><h2 className="section-title">{title}</h2></div>
    <p className="mt-2 text-sm text-slate-600">A previsão ou detecção acima foi calculada pelo modelo especializado. Esta camada apenas transforma o resultado em texto.</p>
    <div className="mt-4 flex flex-wrap items-end gap-3"><label className="text-sm font-semibold">Nível da explicação<select className="mt-1 block rounded-lg border border-slate-300 bg-white p-2" value={level} onChange={event=>setLevel(event.target.value as ExplanationLevel)}>{["Simples","Acadêmica","Técnica"].map(item=><option key={item}>{item}</option>)}</select></label><button className="btn-primary" type="button" onClick={()=>void generate()} disabled={state==="loading"}>{state==="loading"?"Gerando explicação...":"Explicar resultado com IA"}</button></div>
    {state==="idle"&&<p className="mt-4 text-sm text-slate-500">Não gerado.</p>}
    {state==="error"&&<div className="mt-4 rounded-lg bg-rose-50 p-4 text-sm text-rose-900"><p>Não foi possível gerar a explicação externa. {error}</p><button className="btn-secondary mt-3" onClick={()=>void generate("local")}>Usar explicação local</button></div>}
    {result&&<div className="mt-5 rounded-xl border border-fuchsia-100 bg-fuchsia-50/60 p-5"><p className="whitespace-pre-line leading-7 text-slate-800">{result.explanation}</p><p className="mt-4 text-xs font-semibold text-slate-600">Explicação gerada por: {result.mode==="offline"?"Modelo local por regras":result.provider} · {result.mode==="offline"?"Modo local":"Modo externo"}</p>{result.fallback_reason&&<p className="mt-1 text-xs text-amber-800">A explicação externa falhou; foi usada a versão local.</p>}</div>}
  </section>
}
