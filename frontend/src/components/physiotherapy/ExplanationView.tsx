import type { PredictionExplanation } from "../../types/physiotherapyMl";
import { resultLabels } from "./shared";

function formattedImpact(
  value: number,
  unit: PredictionExplanation["impact_unit"],
) {
  const amount = unit === "probability_points" ? value * 100 : value;
  const suffix =
    unit === "probability_points" ? " p.p." : " unidade(s) de escore";
  return `${amount > 0 ? "+" : ""}${amount.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}${suffix}`;
}

export function ExplanationView({
  explanation,
}: {
  explanation: PredictionExplanation;
}) {
  const top = explanation.factors.slice(0, 10);
  const max = Math.max(
    ...top.map((factor) => Math.abs(factor.impact)),
    0.00001,
  );
  return (
    <section className="surface-card space-y-5 p-5 sm:p-7">
      <div>
        <h2 className="section-title">
          Como o modelo chegou a este resultado?
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Contribuições SHAP para a classe{" "}
          {resultLabels[explanation.prediction].toLowerCase()}. Valores
          positivos aumentam o escore desta classe em relação à referência do
          modelo; negativos o reduzem.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <span>← Menor escore da classe</span>
        <span className="text-right">Maior escore da classe →</span>
      </div>
      <div className="space-y-4">
        {top.map((factor) => {
          const width = `${Math.max(2, (Math.abs(factor.impact) / max) * 100)}%`;
          return (
            <div key={factor.feature}>
              <div className="mb-1.5 flex flex-wrap justify-between gap-2 text-sm">
                <span>
                  <strong>{factor.label}</strong> · {String(factor.value)}
                  {factor.feature === "adesao_exercicios" ? "%" : ""}
                </span>
                <span className="text-slate-600">
                  {formattedImpact(factor.impact, explanation.impact_unit)} ·{" "}
                  {factor.intensity}
                </span>
              </div>
              <div
                className="grid h-4 grid-cols-2 gap-0.5"
                aria-label={`${factor.label}: ${formattedImpact(factor.impact, explanation.impact_unit)}`}
              >
                <div className="flex justify-end border-r border-slate-400 bg-slate-50">
                  {factor.impact < 0 && (
                    <div
                      className="h-full rounded-l bg-amber-500"
                      style={{ width }}
                    />
                  )}
                </div>
                <div className="bg-slate-50">
                  {factor.impact > 0 && (
                    <div
                      className="h-full rounded-r bg-ocean-600"
                      style={{ width }}
                    />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="grid gap-4 border-t border-slate-200 pt-5 sm:grid-cols-2">
        <div>
          <h3 className="font-bold">Principais fatores que elevam o escore</h3>
          <p className="mt-1 text-sm text-slate-600">
            {explanation.positive_factors
              .slice(0, 3)
              .map((factor) => factor.label)
              .join(", ") || "Nenhum nesta amostra."}
          </p>
        </div>
        <div>
          <h3 className="font-bold">Principais fatores que reduzem o escore</h3>
          <p className="mt-1 text-sm text-slate-600">
            {explanation.negative_factors
              .slice(0, 3)
              .map((factor) => factor.label)
              .join(", ") || "Nenhum nesta amostra."}
          </p>
        </div>
      </div>
      <p className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-950">
        {explanation.explanation_notice} As intensidades são relativas apenas
        aos impactos deste registro.
      </p>
      {explanation.impact_unit === "logit_units" && (
        <p className="text-sm text-slate-600">
          Para Logistic Regression, os impactos estão em unidades do escore
          interno do classificador, não em pontos percentuais de probabilidade.
        </p>
      )}
    </section>
  );
}
