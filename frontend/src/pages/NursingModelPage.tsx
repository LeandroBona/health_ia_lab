import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { NursingError, NursingHeader, NursingLoading, NursingNav, formatDate } from "../components/nursing/Shared";
import { nursingApi } from "../services/api";
import { signalLabels } from "../types/nursing";
import type { NursingModel, SignalKey } from "../types/nursing";

export function NursingModelPage() {
  const [model, setModel] = useState<NursingModel | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    nursingApi.model().then(setModel).catch((issue: unknown) =>
      setError(issue instanceof Error ? issue.message : "Falha ao carregar modelo."),
    );
  }, []);

  async function retrain() {
    if (!window.confirm("Treinar novamente o Isolation Forest com as medições atuais? A versão será atualizada.")) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const updated = await nursingApi.train();
      setModel(updated);
      setMessage(`Modelo ${updated.version} treinado e medições reanalisadas.`);
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Falha no treinamento.");
    } finally {
      setBusy(false);
    }
  }

  async function analyze() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await nursingApi.analyze();
      setModel(await nursingApi.model());
      setMessage(`${result.total.toLocaleString("pt-BR")} medições analisadas; ${result.anomalies.toLocaleString("pt-BR")} classificadas como anomalia.`);
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Falha na análise.");
    } finally {
      setBusy(false);
    }
  }

  const evaluation = model?.evaluation;
  return <div className="space-y-6">
    <NursingHeader title="Modelo de IA · Enfermagem" subtitle="Isolation Forest aplicado exclusivamente a medições sintéticas. Busca observações diferentes do padrão aprendido." />
    <NursingNav />
    {error && <NursingError message={error} />}
    {message && <p className="rounded-xl bg-teal-50 p-4 text-sm font-semibold text-teal-900" role="status">{message}</p>}
    {!model ? <NursingLoading /> : model.status === "unavailable" ? <NursingError message={model.message ?? "Modelo indisponível."} /> : <>
      <section className="surface-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="section-kicker">Modelo atual</p>
            <h2 className="section-title">Isolation Forest</h2>
            <p className="mt-2 text-sm text-slate-600">Machine Learning não supervisionado · detecção de anomalias</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="btn-secondary" onClick={analyze} disabled={busy}>Reanalisar medições</button>
            <button className="btn-secondary" onClick={retrain} disabled={busy}>Treinar novamente</button>
          </div>
        </div>
        <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {[
            ["Versão", model.version],
            ["Treinamento", model.trained_at ? formatDate(model.trained_at) : "—"],
            ["Registros usados", model.training_records?.toLocaleString("pt-BR")],
            ["Contamination", `${((model.contamination ?? 0) * 100).toFixed(1)}%`],
            ["Anomalias detectadas", model.current_anomalies?.toLocaleString("pt-BR") ?? "—"],
          ].map(([label, value]) => <div className="rounded-xl bg-slate-50 p-4" key={label}>
            <dt className="text-sm text-slate-500">{label}</dt><dd className="mt-1 text-lg font-bold text-slate-900">{value}</dd>
          </div>)}
        </dl>
        <p className="mt-4 text-sm text-slate-600">A taxa <em>contamination</em> orienta o algoritmo para este dataset artificial; não corresponde a uma taxa clínica. O modelo recebe somente dados numéricos e retorna “padrão” ou “anomalia”.</p>
        <div className="mt-5 flex flex-wrap gap-2">
          {model.features?.map(feature => <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-900" key={feature}>{signalLabels[feature as SignalKey]}</span>)}
        </div>
      </section>
      <section className="surface-card p-6">
        <p className="section-kicker">Avaliação educacional</p>
        <h2 className="section-title">Anomalias artificiais x detectadas</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Essa avaliação só é possível porque o dataset sintético conhece quais registros foram artificialmente alterados. A coluna <code>estado</code> não entra no treinamento; ela é usada somente depois para comparar o resultado.</p>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {[["Precision", evaluation?.precision], ["Recall", evaluation?.recall], ["F1-score", evaluation?.f1]].map(([label, value]) =>
            <div className="rounded-xl border border-slate-200 p-5" key={label}>
              <p className="text-sm font-semibold text-slate-500">{label}</p>
              <p className="mt-2 text-3xl font-extrabold text-slate-900">{typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "—"}</p>
            </div>
          )}
        </div>
        <p className="mt-4 text-sm text-slate-600">Precision: das anomalias detectadas, quantas eram alterações artificiais. Recall: das alterações artificiais, quantas foram detectadas. F1 combina ambas.</p>
        <h3 className="mt-7 text-lg font-bold">Matriz de confusão</h3>
        <p className="mt-1 text-sm text-slate-600">Linhas: estado artificial no dataset. Colunas: classificação do modelo.</p>
        <div className="mt-4 overflow-x-auto"><table className="data-table max-w-lg"><thead><tr><th>Estado \ Modelo</th><th>Padrão</th><th>Anomalia</th></tr></thead><tbody>
          <tr><td>Padrão</td><td className="bg-teal-50 font-bold">{evaluation?.confusion_matrix?.[0]?.[0] ?? "—"}</td><td>{evaluation?.confusion_matrix?.[0]?.[1] ?? "—"}</td></tr>
          <tr><td>Alterado</td><td>{evaluation?.confusion_matrix?.[1]?.[0] ?? "—"}</td><td className="bg-teal-50 font-bold">{evaluation?.confusion_matrix?.[1]?.[1] ?? "—"}</td></tr>
        </tbody></table></div>
      </section>
      <section className="surface-card p-6">
        <h2 className="section-title">Como funciona?</h2>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">O Isolation Forest tenta separar registros usando divisões aleatórias. Registros que podem ser isolados rapidamente tendem a ser considerados mais incomuns. Uma anomalia é uma diferença estatística em relação aos dados, nunca um diagnóstico.</p>
        <Link className="btn-primary mt-5" to="/enfermagem/laboratorio">Experimentar no laboratório</Link>
      </section>
    </>}
  </div>;
}
