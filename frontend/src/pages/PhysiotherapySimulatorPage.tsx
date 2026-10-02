import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { physiotherapyApi } from "../services/api";
import type { Patient, Result } from "../types/physiotherapy";
import type {
  EditableFeature,
  FeatureSweep,
  SimulationChanges,
  SimulationResult,
  SweepFeature,
} from "../types/physiotherapyMl";
import {
  ErrorState,
  PhysioHeader,
  ResultBadge,
  columnLabels,
  resultLabels,
} from "../components/physiotherapy/shared";
import {
  ModelNotice,
  percent,
} from "../components/physiotherapy/PredictionPanel";

const classes = Object.keys(resultLabels) as Result[];
const colors: Record<Result, string> = {
  recuperacao_adequada: "#087e8b",
  recuperacao_lenta: "#b7791f",
  abandono: "#b4535c",
};
const controls: {
  key: EditableFeature;
  min: number;
  max: number;
  unit: string;
}[] = [
  { key: "adesao_exercicios", min: 0, max: 100, unit: "%" },
  { key: "faltas", min: 0, max: 30, unit: "" },
  { key: "dor_atual", min: 0, max: 10, unit: "/10" },
  { key: "mobilidade_atual", min: 0, max: 100, unit: "/100" },
  { key: "forca_muscular", min: 1, max: 5, unit: "/5" },
  { key: "sessoes_realizadas", min: 0, max: 30, unit: "" },
  { key: "indice_funcional_atual", min: 0, max: 100, unit: "/100" },
];
const sweepFeatures: SweepFeature[] = [
  "adesao_exercicios",
  "faltas",
  "dor_atual",
  "mobilidade_atual",
  "indice_funcional_atual",
  "sessoes_realizadas",
];
type HistoryEntry = {
  label: string;
  changes: SimulationChanges;
  probabilities: Record<Result, number>;
  prediction: Result;
};

function limits(
  patient: Patient,
  changes: SimulationChanges,
  key: EditableFeature,
): [number, number] {
  const config = controls.find((item) => item.key === key)!;
  if (key === "faltas")
    return [
      0,
      patient.sessoes_previstas -
        (changes.sessoes_realizadas ?? patient.sessoes_realizadas),
    ];
  if (key === "sessoes_realizadas")
    return [0, patient.sessoes_previstas - (changes.faltas ?? patient.faltas)];
  return [config.min, config.max];
}

function preset(patient: Patient, kind: "A" | "B" | "C"): SimulationChanges {
  if (kind === "A")
    return { adesao_exercicios: Math.min(100, patient.adesao_exercicios + 30) };
  if (kind === "B") {
    const faltas = Math.max(0, patient.faltas - 2);
    return {
      faltas,
      sessoes_realizadas: Math.min(
        patient.sessoes_previstas - faltas,
        patient.sessoes_realizadas + 3,
      ),
    };
  }
  return {
    mobilidade_atual: Math.min(100, patient.mobilidade_atual + 20),
    indice_funcional_atual: Math.min(100, patient.indice_funcional_atual + 20),
  };
}

function Comparison({ result }: { result: SimulationResult }) {
  return (
    <section className="surface-card p-5 sm:p-6">
      <h2 className="section-title">Comparação antes/depois</h2>
      {result.class_changed && (
        <p className="mt-4 rounded-xl border border-ocean-200 bg-ocean-50 p-3 text-sm font-semibold text-ocean-900">
          Classificação do modelo alterada:{" "}
          {resultLabels[result.original.prediction]} →{" "}
          {resultLabels[result.simulated.prediction]}.
        </p>
      )}
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        {(["original", "simulated"] as const).map((stage) => (
          <div className="rounded-xl border border-slate-200 p-4" key={stage}>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
              {stage === "original"
                ? "Antes · dados originais"
                : "Depois · cenário simulado"}
            </p>
            <div className="mt-3">
              <ResultBadge result={result[stage].prediction} />
            </div>
            {classes.map((label) => (
              <div className="mt-4" key={label}>
                <div className="mb-1 flex justify-between gap-2 text-sm">
                  <span>{resultLabels[label]}</span>
                  <strong>{percent(result[stage].probabilities[label])}</strong>
                </div>
                <div className="h-2.5 rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${result[stage].probabilities[label] * 100}%`,
                      backgroundColor: colors[label],
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
      <h3 className="mt-6 font-bold">Variação entre as probabilidades</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        {classes.map((label) => (
          <div className="rounded-xl bg-slate-50 p-4" key={label}>
            <p className="text-sm text-slate-600">{resultLabels[label]}</p>
            <p className="mt-1 text-xl font-bold">
              {result.probability_deltas[label] > 0 ? "+" : ""}
              {(result.probability_deltas[label] * 100).toLocaleString(
                "pt-BR",
                { maximumFractionDigits: 1 },
              )}{" "}
              pontos percentuais
            </p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-slate-500">
        Versão do modelo: {result.model_version}. As probabilidades são
        estimativas do classificador, sem calibração clínica.
      </p>
    </section>
  );
}

export function PhysiotherapySimulatorPage() {
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("patientId") ?? "");
  const [patient, setPatient] = useState<Patient | null>(null);
  const [base, setBase] = useState<SimulationResult | null>(null);
  const [changes, setChanges] = useState<SimulationChanges>({});
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [scenarios, setScenarios] = useState<
    { label: string; result: SimulationResult }[]
  >([]);
  const [sweepFeature, setSweepFeature] =
    useState<SweepFeature>("adesao_exercicios");
  const [sweep, setSweep] = useState<FeatureSweep | null>(null);
  const [trackedClass, setTrackedClass] = useState<Result>("recuperacao_lenta");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const counter = useRef(0);

  async function loadPatient(id: string) {
    setBusy(true);
    setError("");
    setPatient(null);
    setResult(null);
    setSweep(null);
    setScenarios([]);
    setHistory([]);
    setChanges({});
    try {
      const found = await physiotherapyApi.patient(id.trim().toUpperCase());
      const initial = await physiotherapyApi.simulate(found.patient_id, {});
      setPatient(found);
      setBase(initial);
      setResult(initial);
      setQuery(found.patient_id);
      counter.current = 0;
      setParams({ patientId: found.patient_id }, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Paciente não encontrado.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    const initial = params.get("patientId");
    if (initial) void loadPatient(initial);
    // Initial deep link is intentionally loaded once. Later selections use loadPatient directly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function randomPatient() {
    setBusy(true);
    setError("");
    try {
      const stats = await physiotherapyApi.stats();
      if (stats.total_patients === 0)
        throw new Error("Ainda não há pacientes para selecionar.");
      const page = Math.floor(Math.random() * stats.total_patients) + 1;
      const result = await physiotherapyApi.patients(
        new URLSearchParams({ page: String(page), page_size: "1" }),
      );
      await loadPatient(result.items[0].patient_id);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao selecionar paciente.",
      );
      setBusy(false);
    }
  }

  async function run(next: SimulationChanges, label?: string) {
    if (!patient) return;
    setBusy(true);
    setError("");
    try {
      const response = await physiotherapyApi.simulate(
        patient.patient_id,
        next,
      );
      setResult(response);
      setChanges(next);
      counter.current += 1;
      setHistory((previous) => [
        ...previous.slice(-7),
        {
          label: label ?? `Simulação ${counter.current}`,
          changes: next,
          probabilities: response.simulated.probabilities,
          prediction: response.simulated.prediction,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na simulação.");
    } finally {
      setBusy(false);
    }
  }

  async function compareScenarios() {
    if (!patient) return;
    setBusy(true);
    setError("");
    try {
      const entries = await Promise.all(
        (["A", "B", "C"] as const).map(async (kind) => ({
          label: `Cenário ${kind}`,
          result: await physiotherapyApi.simulate(
            patient.patient_id,
            preset(patient, kind),
          ),
        })),
      );
      setScenarios(entries);
      setHistory((previous) =>
        [
          ...previous,
          ...entries.map(({ label, result }) => ({
            label,
            changes: result.changes,
            probabilities: result.simulated.probabilities,
            prediction: result.simulated.prediction,
          })),
        ].slice(-8),
      );
      counter.current += entries.length;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao comparar cenários.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function analyzeFeature() {
    if (!patient) return;
    const [, max] = limits(patient, {}, sweepFeature);
    if (max === 0) {
      setError("Não há outro valor válido para esta variável neste registro.");
      return;
    }
    const values = [
      ...new Set(
        Array.from({ length: 11 }, (_, index) =>
          Math.round((max * index) / 10),
        ),
      ),
    ];
    setBusy(true);
    setError("");
    try {
      setSweep(
        await physiotherapyApi.sweepFeature(
          patient.patient_id,
          sweepFeature,
          values,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha na análise de variável.",
      );
    } finally {
      setBusy(false);
    }
  }

  function select(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadPatient(query);
  }
  const originalEntry = base
    ? { label: "Original", ...base.original.probabilities }
    : null;
  const trajectory = originalEntry
    ? [
        originalEntry,
        ...history.map((item) => ({
          label: item.label,
          ...item.probabilities,
        })),
      ]
    : [];
  const scenarioChart = base
    ? [
        { label: "Original", ...base.original.probabilities },
        ...scenarios.map(({ label, result }) => ({
          label,
          ...result.simulated.probabilities,
        })),
      ]
    : [];

  return (
    <div className="space-y-6">
      <PhysioHeader
        back
        title="Simulador de cenários"
        description="Altere valores de um registro fictício e observe a resposta matemática do modelo."
      />
      <ModelNotice />
      <p className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-sm font-semibold leading-6 text-amber-950">
        Alterar uma variável e observar mudança na previsão demonstra apenas o
        comportamento matemático deste modelo educacional. Isso não significa
        que alterar essa variável produziria o mesmo efeito em um paciente real.
      </p>
      <section className="surface-card p-5 sm:p-6">
        <h2 className="section-title">Selecionar paciente</h2>
        <form className="mt-4 flex flex-wrap gap-3" onSubmit={select}>
          <input
            className="field max-w-xs"
            aria-label="Buscar patient_id"
            placeholder="PAC-0042"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button className="btn-primary" disabled={busy} type="submit">
            Buscar paciente
          </button>
          <button
            className="btn-secondary"
            disabled={busy}
            type="button"
            onClick={() => void randomPatient()}
          >
            Paciente aleatório
          </button>
        </form>
      </section>
      {error && <ErrorState message={error} />}
      {busy && !patient && <p role="status">Carregando paciente…</p>}
      {patient && base && (
        <>
          <div className="grid gap-5 xl:grid-cols-3">
            <section className="surface-card p-5">
              <p className="section-kicker">Dados originais</p>
              <h2 className="mt-2 text-xl font-bold">{patient.patient_id}</h2>
              <p className="mt-1 text-sm text-slate-600">
                {patient.idade} anos · {patient.sexo} · {patient.tipo_lesao}
              </p>
              <div className="mt-5 space-y-3">
                {controls.map(({ key, unit }) => (
                  <div
                    className="flex justify-between gap-2 border-b border-slate-100 pb-2 text-sm"
                    key={key}
                  >
                    <span>{columnLabels[key]}</span>
                    <strong>
                      {patient[key]}
                      {unit}
                    </strong>
                  </div>
                ))}
              </div>
            </section>
            <section className="surface-card p-5">
              <p className="section-kicker">Simulação</p>
              <h2 className="mt-2 text-xl font-bold">Modificar variáveis</h2>
              <div className="mt-5 space-y-5">
                {controls.map(({ key, unit }) => {
                  const [min, max] = limits(patient, changes, key);
                  const value = changes[key] ?? patient[key];
                  return (
                    <label className="block" key={key}>
                      <span className="flex justify-between text-sm font-semibold">
                        <span>{columnLabels[key]}</span>
                        <span>
                          {value}
                          {unit}
                        </span>
                      </span>
                      <input
                        className="mt-2 w-full accent-ocean-700"
                        type="range"
                        aria-label={columnLabels[key]}
                        min={min}
                        max={max}
                        step={1}
                        value={value}
                        onChange={(event) => {
                          setChanges((previous) => ({
                            ...previous,
                            [key]: Number(event.target.value),
                          }));
                          setResult(null);
                        }}
                      />
                      <span className="flex justify-between text-xs text-slate-500">
                        <span>{min}</span>
                        <span>{max}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                <button
                  className="btn-primary"
                  disabled={busy}
                  onClick={() => void run(changes)}
                >
                  {busy ? "Calculando…" : "Recalcular previsão"}
                </button>
                <button
                  className="btn-secondary"
                  disabled={busy}
                  onClick={() => {
                    setChanges({});
                    setResult(base);
                  }}
                >
                  Restaurar valores originais
                </button>
              </div>
            </section>
            <section className="surface-card p-5">
              <p className="section-kicker">Resultado</p>
              <h2 className="mt-2 text-xl font-bold">Resposta do modelo</h2>
              {result ? (
                <>
                  <p className="mt-5 text-sm text-slate-600">
                    Classificação do cenário
                  </p>
                  <div className="mt-2">
                    <ResultBadge result={result.simulated.prediction} />
                  </div>
                  <div className="mt-6 space-y-4">
                    {classes.map((label) => (
                      <div key={label}>
                        <div className="flex justify-between gap-2 text-sm">
                          <span>{resultLabels[label]}</span>
                          <strong>
                            {percent(result.simulated.probabilities[label])}
                          </strong>
                        </div>
                        <div className="mt-1 h-2 rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${result.simulated.probabilities[label] * 100}%`,
                              backgroundColor: colors[label],
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="mt-5 text-sm text-slate-600">
                  Valores alterados. Clique em “Recalcular previsão” para
                  atualizar este painel.
                </p>
              )}
            </section>
          </div>
          {result && <Comparison result={result} />}
          <section className="surface-card p-5 sm:p-6">
            <h2 className="section-title">Cenários de demonstração</h2>
            <p className="mt-2 text-sm text-slate-600">
              Cada cenário parte dos dados originais; apenas as variáveis
              indicadas mudam.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                className="btn-secondary"
                disabled={busy}
                onClick={() => void run(preset(patient, "A"), "Cenário A")}
              >
                Cenário A — maior adesão
              </button>
              <button
                className="btn-secondary"
                disabled={busy}
                onClick={() => void run(preset(patient, "B"), "Cenário B")}
              >
                Cenário B — maior participação
              </button>
              <button
                className="btn-secondary"
                disabled={busy}
                onClick={() => void run(preset(patient, "C"), "Cenário C")}
              >
                Cenário C — indicadores diferentes
              </button>
              <button
                className="btn-primary"
                disabled={busy}
                onClick={() => void compareScenarios()}
              >
                Comparar A, B e C
              </button>
            </div>
            {scenarios.length > 0 && (
              <>
                <div
                  className="mt-5 h-72"
                  role="img"
                  aria-label="Comparação das probabilidades por cenário"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={scenarioChart}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" />
                      <YAxis
                        tickFormatter={(value: number) =>
                          `${Math.round(value * 100)}%`
                        }
                      />
                      <Tooltip formatter={(value) => percent(Number(value))} />
                      <Legend />
                      {classes.map((label) => (
                        <Bar
                          key={label}
                          dataKey={label}
                          name={resultLabels[label]}
                          fill={colors[label]}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Cenário</th>
                        {classes.map((label) => (
                          <th key={label}>{resultLabels[label]}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {scenarioChart.map((row) => (
                        <tr key={row.label}>
                          <th>{row.label}</th>
                          {classes.map((label) => (
                            <td key={label}>{percent(row[label])}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
          <section className="surface-card p-5 sm:p-6">
            <h2 className="section-title">Histórico de cenários</h2>
            <p className="mt-2 text-sm text-slate-600">
              As últimas oito simulações ficam apenas nesta página enquanto ela
              estiver aberta. Nenhum valor é salvo no banco.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                {
                  label: "Original",
                  changes: {},
                  probabilities: base.original.probabilities,
                  prediction: base.original.prediction,
                },
                ...history,
              ].map((entry, index) => (
                <div
                  className="rounded-xl border border-slate-200 px-4 py-3 text-sm"
                  key={`${entry.label}-${index}`}
                >
                  <strong>{entry.label}</strong>
                  <p>{resultLabels[entry.prediction]}</p>
                  <p>
                    Adesão{" "}
                    {entry.changes.adesao_exercicios ??
                      patient.adesao_exercicios}
                    % · {percent(entry.probabilities[trackedClass])} em{" "}
                    {resultLabels[trackedClass].toLowerCase()}
                  </p>
                </div>
              ))}
            </div>
            <label className="field-label mt-5 block max-w-sm">
              Classe na trajetória
              <select
                className="field mt-1"
                value={trackedClass}
                onChange={(event) =>
                  setTrackedClass(event.target.value as Result)
                }
              >
                {classes.map((label) => (
                  <option value={label} key={label}>
                    {resultLabels[label]}
                  </option>
                ))}
              </select>
            </label>
            <div
              className="mt-4 h-64"
              role="img"
              aria-label={`Trajetória da probabilidade de ${resultLabels[trackedClass]}`}
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trajectory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" />
                  <YAxis
                    domain={[0, 1]}
                    tickFormatter={(value: number) =>
                      `${Math.round(value * 100)}%`
                    }
                  />
                  <Tooltip formatter={(value) => percent(Number(value))} />
                  <Line
                    type="linear"
                    dataKey={trackedClass}
                    name={resultLabels[trackedClass]}
                    stroke={colors[trackedClass]}
                    strokeWidth={3}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
          <section className="surface-card p-5 sm:p-6">
            <h2 className="section-title">
              Explorar influência de uma variável
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Este gráfico demonstra como o modelo responde quando apenas uma
              variável é alterada e todas as demais permanecem constantes.
            </p>
            <div className="mt-4 flex flex-wrap items-end gap-3">
              <label className="field-label block w-full max-w-sm">
                Variável
                <select
                  className="field mt-1"
                  value={sweepFeature}
                  onChange={(event) => {
                    setSweepFeature(event.target.value as SweepFeature);
                    setSweep(null);
                  }}
                >
                  {sweepFeatures.map((feature) => (
                    <option key={feature} value={feature}>
                      {columnLabels[feature]}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="btn-primary"
                disabled={busy}
                onClick={() => void analyzeFeature()}
              >
                Calcular sensibilidade
              </button>
            </div>
            {sweep && (
              <div
                className="mt-5 h-80"
                role="img"
                aria-label={`Sensibilidade do modelo para ${columnLabels[sweep.feature]}`}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sweep.points}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="value"
                      label={{
                        value: columnLabels[sweep.feature],
                        position: "insideBottom",
                        offset: -4,
                      }}
                    />
                    <YAxis
                      domain={[0, 1]}
                      tickFormatter={(value: number) =>
                        `${Math.round(value * 100)}%`
                      }
                    />
                    <Tooltip formatter={(value) => percent(Number(value))} />
                    <Legend />
                    {classes.map((label) => (
                      <Line
                        key={label}
                        type="linear"
                        dataKey={`probabilities.${label}`}
                        name={resultLabels[label]}
                        stroke={colors[label]}
                        strokeWidth={2}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
