import { useState } from "react";
import type { FormEvent } from "react";
import type { DatasetSchema } from "../../types/physiotherapy";
import type {
  PatientFeatures,
  Prediction,
  PredictionExplanation,
} from "../../types/physiotherapyMl";
import { physiotherapyApi } from "../../services/api";
import { columnLabels, ErrorState } from "./shared";
import { PredictionResult } from "./PredictionPanel";
import { ExplanationView } from "./ExplanationView";

const defaults: PatientFeatures = {
  idade: 67,
  sexo: "Masculino",
  tipo_lesao: "Joelho",
  tempo_lesao_dias: 150,
  dor_inicial: 8,
  dor_atual: 6,
  mobilidade_inicial: 43,
  mobilidade_atual: 52,
  forca_muscular: 3,
  sessoes_previstas: 15,
  sessoes_realizadas: 7,
  faltas: 4,
  adesao_exercicios: 38,
  comorbidades: 2,
  indice_funcional_inicial: 35,
  indice_funcional_atual: 44,
};
type NumericKey = Exclude<keyof PatientFeatures, "sexo" | "tipo_lesao">;
const limits: Record<NumericKey, [number, number]> = {
  idade: [18, 85],
  tempo_lesao_dias: [1, 730],
  dor_inicial: [0, 10],
  dor_atual: [0, 10],
  mobilidade_inicial: [0, 100],
  mobilidade_atual: [0, 100],
  forca_muscular: [1, 5],
  sessoes_previstas: [5, 30],
  sessoes_realizadas: [0, 30],
  faltas: [0, 30],
  adesao_exercicios: [0, 100],
  comorbidades: [0, 5],
  indice_funcional_inicial: [0, 100],
  indice_funcional_atual: [0, 100],
};

export function ManualPrediction({ schema }: { schema: DatasetSchema }) {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [explainedFeatures, setExplainedFeatures] =
    useState<PatientFeatures | null>(null);
  const [explanation, setExplanation] = useState<PredictionExplanation | null>(
    null,
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const features: PatientFeatures = {
      ...defaults,
      sexo: String(form.get("sexo")),
      tipo_lesao: String(form.get("tipo_lesao")),
    };
    for (const key of Object.keys(limits) as NumericKey[])
      features[key] = Number(form.get(key));
    setPrediction(null);
    setExplanation(null);
    setExplainedFeatures(null);
    setError("");
    if (
      features.sessoes_realizadas + features.faltas >
      features.sessoes_previstas
    ) {
      setError(
        "Sessões realizadas + faltas não podem exceder as sessões previstas.",
      );
      return;
    }
    setBusy(true);
    try {
      setPrediction(await physiotherapyApi.predict(features));
      setExplainedFeatures(features);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na previsão.");
    } finally {
      setBusy(false);
    }
  }
  async function explain() {
    if (!explainedFeatures) return;
    setBusy(true);
    setError("");
    try {
      setExplanation(await physiotherapyApi.explainManual(explainedFeatures));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao explicar a previsão.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="surface-card p-5 sm:p-7">
      <h2 className="section-title">Previsão manual</h2>
      <p className="mb-5 mt-2 text-sm leading-6 text-slate-600">
        Altere os dados do exemplo sintético para observar a classificação. Este
        formulário não salva pacientes no banco.
      </p>
      <form
        onSubmit={(event) => void submit(event)}
        onChange={() => {
          setPrediction(null);
          setExplanation(null);
          setExplainedFeatures(null);
        }}
      >
        <fieldset
          disabled={busy}
          className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
        >
          {(Object.keys(defaults) as (keyof PatientFeatures)[]).map((key) => (
            <label className="field-label" key={key}>
              {columnLabels[key]}
              {key === "sexo" || key === "tipo_lesao" ? (
                <select
                  className="field mt-1"
                  name={key}
                  defaultValue={defaults[key]}
                >
                  {(key === "sexo" ? schema.sexes : schema.injuries).map(
                    (option) => (
                      <option key={option}>{option}</option>
                    ),
                  )}
                </select>
              ) : (
                <input
                  className="field mt-1"
                  name={key}
                  type="number"
                  required
                  step={1}
                  min={limits[key][0]}
                  max={limits[key][1]}
                  defaultValue={defaults[key]}
                />
              )}
            </label>
          ))}
        </fieldset>
        <button className="btn-primary mt-5" disabled={busy} type="submit">
          {busy ? "Classificando…" : "Classificar registro fictício"}
        </button>
      </form>
      {error && (
        <div className="mt-5">
          <ErrorState message={error} />
        </div>
      )}
      {prediction && (
        <div className="mt-6 border-t border-slate-200 pt-6">
          <PredictionResult prediction={prediction} />
          <button
            type="button"
            className="btn-secondary mt-5"
            disabled={busy}
            onClick={() => void explain()}
          >
            {busy ? "Calculando SHAP…" : "Explicar esta previsão"}
          </button>
        </div>
      )}
      {explanation && (
        <div className="mt-5">
          <ExplanationView explanation={explanation} />
        </div>
      )}
    </section>
  );
}
