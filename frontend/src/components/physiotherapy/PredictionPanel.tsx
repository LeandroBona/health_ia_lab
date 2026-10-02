import { useEffect, useState } from "react";
import { BrainCircuit } from "lucide-react";
import { Link } from "react-router-dom";
import { physiotherapyApi } from "../../services/api";
import type {
  Prediction,
  PredictionExplanation,
} from "../../types/physiotherapyMl";
import type { Result } from "../../types/physiotherapy";
import { ErrorState, Progress, ResultBadge, resultLabels } from "./shared";
import { ExplanationView } from "./ExplanationView";
import { AIExplanationCard } from "../AIExplanationCard";

export const modelNotice =
  "Este modelo foi treinado exclusivamente com dados sintéticos e relações artificialmente construídas para fins educacionais. Seus resultados não possuem validade clínica.";
export const algorithmLabel = (name: string) =>
  name === "RandomForestClassifier"
    ? "Random Forest"
    : name === "LogisticRegression"
      ? "Logistic Regression"
      : name;
export const percent = (value: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);

export function ModelNotice() {
  return (
    <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950">
      {modelNotice}
    </p>
  );
}

export function PredictionResult({ prediction }: { prediction: Prediction }) {
  const sorted = Object.values(prediction.probabilities).sort((a, b) => b - a);
  const gap = sorted[0] - sorted[1];
  return (
    <div className="space-y-5" role="status">
      <div className="rounded-2xl bg-ink p-6 text-white">
        <p className="text-sm font-bold tracking-widest text-ocean-200">
          RESULTADO DO MODELO
        </p>
        <h3 className="mt-3 text-2xl font-bold">
          {resultLabels[prediction.prediction]}
        </h3>
        <p className="mt-3 text-base leading-7 text-slate-300">
          O modelo classificou este registro como{" "}
          {resultLabels[prediction.prediction].toLowerCase()}. Essa foi a classe
          com maior probabilidade entre os padrões artificiais aprendidos.
        </p>
        <p className="mt-4 font-semibold">
          Maior probabilidade: {percent(prediction.confidence)}
        </p>
        <p className="mt-2 text-sm leading-6 text-slate-300">
          {gap < 0.1
            ? "Previsão com probabilidades próximas; resultado pouco definido pelo modelo."
            : gap < 0.25
              ? "Resultado moderadamente definido entre as classes."
              : "Resultado mais concentrado em uma classe."}{" "}
          Essa comparação usa apenas a distância matemática entre as duas
          maiores probabilidades; não é garantia de acerto nem probabilidade
          clínica calibrada.
        </p>
        <p className="mt-4 text-sm text-ocean-200">
          {algorithmLabel(prediction.algorithm)} · versão{" "}
          {prediction.model_version}
        </p>
      </div>
      <section className="space-y-4">
        <h3 className="font-bold">Probabilidades por classe</h3>
        {(Object.keys(resultLabels) as Result[]).map((label) => (
          <div key={label}>
            <div className="mb-2 flex justify-between gap-3 text-sm">
              <span>{resultLabels[label]}</span>
              <strong>{percent(prediction.probabilities[label])}</strong>
            </div>
            <Progress
              label={`Probabilidade de ${resultLabels[label]}`}
              value={prediction.probabilities[label] * 100}
            />
          </div>
        ))}
      </section>
      {prediction.actual_result && (
        <div className="rounded-xl border border-slate-200 p-5">
          <h3 className="font-bold">Registro × previsão</h3>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
            <span>Resultado registrado:</span>
            <ResultBadge result={prediction.actual_result} />
          </div>
          <p className="mt-4 text-base font-semibold">
            {prediction.correct
              ? "Acerto: a classe prevista coincide com o resultado registrado."
              : "Erro: a classe prevista difere do resultado registrado."}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {prediction.partition === "train"
              ? "Este registro participou do treino. Um acerto aqui não demonstra desempenho em dados novos."
              : prediction.partition === "test"
                ? "Este registro pertence à divisão de teste usada na avaliação e seleção do algoritmo."
                : "Este registro é novo ou foi alterado após o treino. As métricas salvas se referem ao dataset anterior."}
          </p>
        </div>
      )}
    </div>
  );
}

export function PatientPrediction({ patientId }: { patientId: string }) {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [explanation, setExplanation] = useState<PredictionExplanation | null>(
    null,
  );
  const [explaining, setExplaining] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setPrediction(null);
    setExplanation(null);
    setError("");
  }, [patientId]);
  async function run() {
    setBusy(true);
    setError("");
    setPrediction(null);
    setExplanation(null);
    try {
      setPrediction(await physiotherapyApi.predictPatient(patientId));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao executar a análise.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function explain() {
    setExplaining(true);
    setError("");
    try {
      setExplanation(await physiotherapyApi.explainPatient(patientId));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao explicar a previsão.",
      );
    } finally {
      setExplaining(false);
    }
  }
  return (
    <section className="surface-card space-y-5 p-5 sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <BrainCircuit className="text-ocean-700" />
            <h2 className="section-title">Análise por Machine Learning</h2>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Classificação didática dos dados registrados. O resultado original
            não é fornecido como entrada ao modelo.
          </p>
        </div>
        <button
          className="btn-primary"
          disabled={busy}
          onClick={() => void run()}
        >
          {busy ? "Analisando…" : "Executar análise"}
        </button>
      </div>
      <ModelNotice />
      <p className="text-sm leading-6 text-slate-600">
        O modelo usa também os indicadores atuais para classificar o registro.
        Esta demonstração não estima uma evolução futura ao longo do tempo.
      </p>
      {error && <ErrorState message={error} />}
      {prediction && <PredictionResult prediction={prediction} />}
      {prediction && (
        <div className="flex flex-wrap gap-3 border-t border-slate-200 pt-5">
          <button
            className="btn-secondary"
            disabled={explaining}
            onClick={() => void explain()}
          >
            {explaining ? "Calculando SHAP…" : "Explicar esta previsão"}
          </button>
          <Link
            className="btn-primary"
            to={`/fisioterapia/simulador?patientId=${encodeURIComponent(patientId)}`}
          >
            Simular alterações
          </Link>
        </div>
      )}
      {explanation && <ExplanationView explanation={explanation} />}
      {prediction && <AIExplanationCard title="Explicar resultado com IA" module="fisioterapia" analysisType="prediction" recordReference={patientId} sourceData={{prediction:prediction.prediction,probabilities:prediction.probabilities,algorithm:prediction.algorithm,factors:explanation?.factors.slice(0,3).map(factor=>({label:factor.label,feature:factor.feature,value:factor.value}))??[]}} />}
    </section>
  );
}
