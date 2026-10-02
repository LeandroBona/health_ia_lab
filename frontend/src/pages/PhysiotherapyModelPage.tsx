import { useEffect, useState } from "react";
import { Info, Play, BrainCircuit } from "lucide-react";
import { physiotherapyApi } from "../services/api";
import type { ModelEvaluation, ModelInfo } from "../types/physiotherapyMl";
import type { DatasetSchema } from "../types/physiotherapy";
import {
  ErrorState,
  LoadingState,
  PhysioHeader,
  columnLabels,
  number,
  resultLabels,
} from "../components/physiotherapy/shared";
import {
  ModelNotice,
  algorithmLabel,
  percent,
} from "../components/physiotherapy/PredictionPanel";
import { ManualPrediction } from "../components/physiotherapy/ManualPrediction";
import type { GlobalFeatureImportance } from "../types/physiotherapyMl";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const explanations = {
  accuracy: "Percentual total de previsões corretas.",
  precision_macro:
    "Entre os registros classificados em determinada categoria, quantos realmente pertenciam a ela. Macro: média das três classes, com o mesmo peso.",
  recall_macro:
    "Entre os registros que realmente pertenciam a uma categoria, quantos o modelo conseguiu identificar. Macro: média das três classes, com o mesmo peso.",
  f1_macro:
    "Métrica que combina precision e recall. Macro: média das três classes, com o mesmo peso; usada para selecionar o modelo.",
};
const metricNames = {
  accuracy: "Accuracy",
  precision_macro: "Precision macro",
  recall_macro: "Recall macro",
  f1_macro: "F1-score macro",
};
type Metric = keyof typeof metricNames;

export function PhysiotherapyModelPage() {
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [evaluation, setEvaluation] = useState<ModelEvaluation | null>(null);
  const [schema, setSchema] = useState<DatasetSchema | null>(null);
  const [importance, setImportance] = useState<GlobalFeatureImportance | null>(
    null,
  );
  const [importanceError, setImportanceError] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [message, setMessage] = useState("");
  const [info, setInfo] = useState<Metric | null>(null);
  useEffect(() => {
    let active = true;
    setError("");
    setImportance(null);
    setImportanceError("");
    Promise.all([physiotherapyApi.model(), physiotherapyApi.schema()])
      .then(async ([modelData, schemaData]) => {
        if (!active) return;
        setModel(modelData);
        setSchema(schemaData);
        if (modelData.status === "ready") {
          const result = await physiotherapyApi.evaluation();
          if (active) setEvaluation(result);
          physiotherapyApi
            .featureImportance()
            .then((data) => {
              if (active) setImportance(data);
            })
            .catch((err: unknown) => {
              if (active)
                setImportanceError(
                  err instanceof Error
                    ? err.message
                    : "Não foi possível calcular a importância das variáveis.",
                );
            });
        } else setEvaluation(null);
      })
      .catch((err: unknown) => {
        if (active)
          setError(
            err instanceof Error
              ? err.message
              : "Não foi possível carregar o modelo.",
          );
      });
    return () => {
      active = false;
    };
  }, [revision]);
  async function train() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await physiotherapyApi.train();
      setMessage(
        `Treinamento concluído em ${number(result.training_seconds)} s. Modelo selecionado: ${algorithmLabel(result.selected_model)}, versão ${result.version}.`,
      );
      setRevision((value) => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no treinamento.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-6">
      <PhysioHeader
        back
        title="Modelo de IA"
        description="Treine, compare e avalie classificadores usando relações artificiais dos registros de Fisioterapia."
      >
        <button
          className="btn-primary"
          disabled={busy}
          onClick={() => void train()}
        >
          <Play size={17} />
          {busy ? "Treinando os dois algoritmos…" : "Treinar com dados atuais"}
        </button>
      </PhysioHeader>
      <ModelNotice />
      <p className="text-sm leading-6 text-slate-600">
        Treinamento manual usa todos os pacientes atuais do banco, com divisão
        estratificada de 80% para treino e 20% para teste. Um novo treino
        substitui o modelo ativo e incrementa sua versão.
      </p>
      {error && (
        <ErrorState
          message={error}
          retry={() => setRevision((value) => value + 1)}
        />
      )}
      {message && (
        <p
          className="rounded-xl bg-emerald-50 p-4 text-emerald-900"
          role="status"
        >
          {message}
        </p>
      )}
      {!model && !error && <LoadingState />}
      {model?.status === "unavailable" && (
        <ErrorState message={model.message} />
      )}
      {model?.status === "ready" && (
        <>
          <section className="surface-card p-6">
            <div className="flex items-center gap-3">
              <BrainCircuit className="text-ocean-700" />
              <h2 className="section-title">
                Modelo atual · {algorithmLabel(model.algorithm)}
              </h2>
            </div>
            <dl className="mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["Versão", model.version],
                [
                  "Data de treinamento",
                  new Date(model.trained_at).toLocaleString("pt-BR"),
                ],
                [
                  "Dataset utilizado",
                  model.dataset_source === "default"
                    ? "Padrão de Fisioterapia"
                    : "Fisioterapia · banco completo",
                ],
                ["Registros", number(model.record_count)],
                [
                  "Treino / teste",
                  `${model.training_samples} / ${model.test_samples}`,
                ],
                ["Seed da divisão", model.random_state],
                ["Tempo de treinamento", `${number(model.training_seconds)} s`],
                ["Seleção", "Maior F1-score macro"],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt className="text-sm text-slate-500">{label}</dt>
                  <dd className="mt-1 font-semibold">{value}</dd>
                </div>
              ))}
            </dl>
            <details className="mt-5 border-t border-slate-100 pt-4">
              <summary className="cursor-pointer font-semibold">
                {model.features.length} variáveis utilizadas
              </summary>
              <div className="mt-3 flex flex-wrap gap-2">
                {model.features.map((key) => (
                  <span
                    className="rounded-lg bg-slate-100 px-3 py-2 text-sm"
                    key={key}
                  >
                    {columnLabels[key]}
                  </span>
                ))}
              </div>
              <p className="mt-3 text-sm text-slate-500">
                patient_id e resultado não são variáveis preditoras.
              </p>
            </details>
          </section>
          {model.dataset_changed && (
            <p
              role="status"
              className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-900"
            >
              Os dados usados como fonte mudaram desde o treinamento. As
              métricas e previsões continuam associadas à versão {model.version}
              . Treine novamente para atualizar o modelo.
            </p>
          )}
          <section className="surface-card p-6">
            <h2 className="section-title">Como o modelo utiliza os dados?</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Esta visualização usa uma amostra de até 60 registros do conjunto
              de teste e mostra a magnitude média das contribuições SHAP,
              reunida por variável original.
            </p>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4">
                <h3 className="font-bold">Explicação global</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Mostra quais variáveis são mais relevantes considerando várias
                  previsões.
                </p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <h3 className="font-bold">Explicação individual</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Mostra quais variáveis mais influenciaram a classificação de
                  um registro específico.
                </p>
              </div>
            </div>
          </section>
          <section className="surface-card p-6">
            <h2 className="section-title">
              Variáveis mais utilizadas pelo modelo
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              As 10 variáveis com maior participação relativa nas explicações da
              amostra de teste.
            </p>
            {importanceError && (
              <div className="mt-4">
                <ErrorState message={importanceError} />
              </div>
            )}
            {!importance && !importanceError && (
              <div className="mt-4">
                <LoadingState />
              </div>
            )}
            {importance && (
              <div
                className="mt-5 h-[420px]"
                role="img"
                aria-label="Importância global das 10 principais variáveis"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={importance.features.slice(0, 10).reverse()}
                    layout="vertical"
                    margin={{ left: 16, right: 28 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis
                      type="number"
                      tickFormatter={(value: number) =>
                        `${Math.round(value * 100)}%`
                      }
                      domain={[0, "dataMax"]}
                    />
                    <YAxis
                      type="category"
                      dataKey="label"
                      width={170}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip
                      formatter={(value) =>
                        `${(Number(value) * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`
                      }
                    />
                    <Bar
                      dataKey="importance"
                      name="Participação relativa"
                      fill="#087e8b"
                      radius={[0, 6, 6, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
            {importance && (
              <p className="mt-2 text-xs text-slate-500">
                Amostra de teste: {importance.sample_size} registros · versão{" "}
                {importance.model_version}.
              </p>
            )}
            <p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-950">
              Importância de uma variável indica o quanto ela é utilizada pelo
              modelo para realizar classificações. Isso não significa que a
              variável cause o resultado.
            </p>
          </section>
          {evaluation && (
            <>
              <section
                className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
                aria-label="Métricas de teste"
              >
                {(Object.keys(metricNames) as Metric[]).map((key) => (
                  <article className="surface-card p-5" key={key}>
                    <div className="flex items-center justify-between gap-3">
                      <h2 className="text-sm font-semibold text-slate-600">
                        {metricNames[key]}
                      </h2>
                      <button
                        className="rounded-full p-1 text-ocean-700"
                        aria-label={`Sobre ${metricNames[key]}`}
                        aria-expanded={info === key}
                        onClick={() => setInfo(info === key ? null : key)}
                      >
                        <Info size={19} />
                      </button>
                    </div>
                    <p className="mt-3 text-3xl font-bold">
                      {percent(evaluation[key])}
                    </p>
                    {info === key && (
                      <p className="mt-3 text-sm leading-6 text-slate-600">
                        {explanations[key]}
                      </p>
                    )}
                  </article>
                ))}
              </section>
              <p className="text-sm leading-6 text-slate-600">
                {evaluation.evaluation_note}
              </p>
              <section className="surface-card overflow-hidden">
                <div className="p-6">
                  <h2 className="section-title">Matriz de Confusão</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    Linhas representam o resultado registrado no dataset.
                    Colunas representam a previsão realizada pelo modelo.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <caption className="px-6 pb-4 text-left text-sm text-slate-500">
                      {evaluation.test_samples} registros de teste · real ↓ /
                      previsto →
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Real / previsto</th>
                        {evaluation.classes.map((label) => (
                          <th scope="col" key={label}>
                            {resultLabels[label]}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {evaluation.classes.map((label, rowIndex) => (
                        <tr key={label}>
                          <th scope="row">{resultLabels[label]}</th>
                          {evaluation.confusion_matrix[rowIndex].map(
                            (count, columnIndex) => (
                              <td
                                key={columnIndex}
                                className={
                                  rowIndex === columnIndex
                                    ? "bg-ocean-50 font-bold text-ocean-900"
                                    : "text-slate-600"
                                }
                              >
                                {count}
                                {rowIndex === columnIndex && (
                                  <span className="ml-2 text-xs">acertos</span>
                                )}
                              </td>
                            ),
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
              <section className="surface-card overflow-hidden">
                <h2 className="section-title p-6">Comparação de algoritmos</h2>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Algoritmo</th>
                        <th>Accuracy</th>
                        <th>Precision macro</th>
                        <th>Recall macro</th>
                        <th>F1 macro</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(evaluation.algorithms).map(
                        ([algorithm, metrics]) => (
                          <tr
                            key={algorithm}
                            className={
                              algorithm === evaluation.selected_model
                                ? "bg-ocean-50"
                                : ""
                            }
                          >
                            <td className="font-semibold">
                              {algorithmLabel(algorithm)}
                              {algorithm === evaluation.selected_model && (
                                <span className="ml-3 rounded-full bg-ocean-100 px-2 py-1 text-xs text-ocean-900">
                                  Modelo selecionado
                                </span>
                              )}
                            </td>
                            {(Object.keys(metricNames) as Metric[]).map(
                              (key) => (
                                <td key={key}>{percent(metrics[key])}</td>
                              ),
                            )}
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
              <section className="surface-card overflow-hidden">
                <h2 className="section-title p-6">
                  Métricas por classe · modelo selecionado
                </h2>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Classe</th>
                        <th>Precision</th>
                        <th>Recall</th>
                        <th>F1-score</th>
                        <th>Registros de teste</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evaluation.classes.map((label) => (
                        <tr key={label}>
                          <td>{resultLabels[label]}</td>
                          <td>
                            {percent(evaluation.per_class[label].precision)}
                          </td>
                          <td>{percent(evaluation.per_class[label].recall)}</td>
                          <td>{percent(evaluation.per_class[label].f1)}</td>
                          <td>{evaluation.per_class[label].support}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
          {schema && <ManualPrediction key={model.version} schema={schema} />}
        </>
      )}
    </div>
  );
}
