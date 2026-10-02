import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { AnalysisView, PsychologyHeader, PsychologyNav, PsychologyNotice } from "../components/psychology/Shared";
import { psychologyApi } from "../services/api";
import type { PsychologyDetail } from "../types/psychology";

export function PsychologyRecordPage() {
  const { recordId } = useParams();
  const [record, setRecord] = useState<PsychologyDetail | null>(null);
  const [error, setError] = useState("");
  const [showProcessing, setShowProcessing] = useState(false);
  useEffect(() => { if (recordId) psychologyApi.record(recordId).then(setRecord).catch(e => setError(e instanceof Error ? e.message : String(e))); }, [recordId]);
  return <div className="space-y-6"><PsychologyHeader title={`Relato ${recordId ?? ""}`} subtitle="Exploração linguística de um registro inteiramente fictício."/><PsychologyNav/><PsychologyNotice/>
    {error && <p className="rounded-xl bg-rose-50 p-4 text-rose-800">{error}</p>}
    {record && <><section className="surface-card p-6"><h2 className="section-title">Dados do registro</h2><dl className="mt-4 grid gap-4 text-sm md:grid-cols-3"><div><dt className="font-bold">Faixa etária</dt><dd>{record.idade_faixa ?? "—"}</dd></div><div><dt className="font-bold">Contexto sintético</dt><dd>{record.contexto}</dd></div><div><dt className="font-bold">Data sintética</dt><dd>{record.data_sintetica ?? "—"}</dd></div><div><dt className="font-bold">Tema registrado</dt><dd>{record.tema_principal}</dd></div><div><dt className="font-bold">Tema secundário</dt><dd>{record.tema_secundario ?? "—"}</dd></div><div><dt className="font-bold">Comparação</dt><dd>{record.correct ? "Classificação igual ao registro" : "Classificação diferente do registro"}</dd></div></dl></section>
      <section className="surface-card p-6"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="section-title">Análise por NLP</h2><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={showProcessing} onChange={e => setShowProcessing(e.target.checked)}/>Mostrar processamento</label></div><div className="mt-5"><AnalysisView analysis={record.analysis} showProcessing={showProcessing} recordReference={recordId}/></div></section></>}
  </div>;
}
