import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  Database,
  Download,
  Upload,
  Users,
  Activity,
  Calendar,
  ClipboardCheck,
} from "lucide-react";
import { physiotherapyApi } from "../services/api";
import type {
  DatasetInfo,
  DatasetSchema,
  PhysioStats,
} from "../types/physiotherapy";
import { MetricCard } from "../components/MetricCard";
import {
  ErrorState,
  LoadingState,
  PhysioHeader,
  number,
} from "../components/physiotherapy/shared";
import { PhysioCharts } from "../components/physiotherapy/Charts";
import { PatientsTable } from "../components/physiotherapy/PatientsTable";

export function PhysiotherapyPage() {
  const [data, setData] = useState<{
    stats: PhysioStats;
    schema: DatasetSchema;
    dataset: DatasetInfo;
  } | null>(null);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [size, setSize] = useState(1000);
  const [seed, setSeed] = useState(42);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [regenError, setRegenError] = useState("");
  useEffect(() => {
    let active = true;
    setError("");
    Promise.all([
      physiotherapyApi.stats(),
      physiotherapyApi.schema(),
      physiotherapyApi.dataset(),
    ])
      .then(([stats, schema, dataset]) => {
        if (active) {
          setData({ stats, schema, dataset });
          setSize(dataset.size);
          setSeed(dataset.seed ?? 42);
        }
      })
      .catch((err: unknown) => {
        if (active)
          setError(
            err instanceof Error
              ? err.message
              : "Não foi possível carregar o módulo.",
          );
      });
    return () => {
      active = false;
    };
  }, [revision]);
  async function regenerate() {
    setBusy(true);
    setMessage("");
    setRegenError("");
    try {
      const result = await physiotherapyApi.regenerate(size, seed);
      setMessage(
        `Dataset regenerado: ${number(result.imported)} pacientes padrão salvos; ${number(result.ignored)} IDs preservados por já pertencerem a importações.`,
      );
      setConfirm(false);
      setRevision((value) => value + 1);
    } catch (err) {
      setRegenError(
        err instanceof Error ? err.message : "Falha na regeneração.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-6">
      <PhysioHeader
        title="Fisioterapia"
        description="Análise de dados sintéticos de pacientes em acompanhamento fisioterapêutico."
      >
        <div className="flex flex-wrap gap-2">
          <Link className="btn-secondary" to="/fisioterapia/explorar">
            <BarChart3 size={18} />
            Explorar Dataset
          </Link>
          <Link className="btn-primary" to="/fisioterapia/importar">
            <Upload size={18} />
            Importar planilha
          </Link>
        </div>
      </PhysioHeader>
      {error ? (
        <ErrorState
          message={error}
          retry={() => setRevision((value) => value + 1)}
        />
      ) : !data ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-3">
            {[
              {
                label: "Total de pacientes",
                value: data.stats.total_patients,
                helper: "Registros sintéticos no banco",
                icon: Users,
              },
              {
                label: "Idade média",
                value: data.stats.average_age,
                helper: "Anos · todos os registros",
                icon: Calendar,
              },
              {
                label: "Dor média inicial",
                value: data.stats.average_pain_initial,
                helper: "Escala de 0 a 10",
                icon: Activity,
              },
              {
                label: "Dor média atual",
                value: data.stats.average_pain_current,
                helper: "Escala de 0 a 10",
                icon: Activity,
              },
              {
                label: "Adesão média",
                value: data.stats.average_adherence,
                helper: "Percentual de 0 a 100",
                icon: BarChart3,
              },
              {
                label: "Resultados registrados",
                value: data.stats.registered_results,
                helper: "Rótulos artificiais, não previsões",
                icon: ClipboardCheck,
              },
            ].map((metric) => (
              <MetricCard
                key={metric.label}
                {...metric}
                tone="bg-ocean-50 text-ocean-700"
              />
            ))}
          </div>
          <PhysioCharts stats={data.stats} />
          <PatientsTable schema={data.schema} revision={revision} />
          <section className="surface-card p-5 sm:p-7">
            <div className="flex flex-wrap justify-between gap-5">
              <div>
                <div className="flex items-center gap-3">
                  <Database className="text-ocean-700" />
                  <h2 className="section-title">Dataset educacional padrão</h2>
                </div>
                <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-3 text-sm">
                  <div>
                    <dt className="text-slate-500">Pacientes no arquivo</dt>
                    <dd className="mt-1 text-xl font-bold">
                      {number(data.dataset.size)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Formato</dt>
                    <dd className="mt-1 font-semibold">Sintético</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Área</dt>
                    <dd className="mt-1 font-semibold">Fisioterapia</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Seed</dt>
                    <dd className="mt-1 font-semibold">
                      {data.dataset.seed ?? "Arquivo existente"}
                    </dd>
                  </div>
                </dl>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <a
                  className="btn-secondary"
                  href={physiotherapyApi.downloadUrl("csv")}
                >
                  <Download size={17} />
                  Baixar CSV
                </a>
                <a
                  className="btn-secondary"
                  href={physiotherapyApi.downloadUrl("xlsx")}
                >
                  <Download size={17} />
                  Baixar XLSX
                </a>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-500">
              Os downloads contêm apenas o dataset padrão. A tabela e os
              gráficos incluem também as importações confirmadas.
            </p>
            <details className="mt-5 border-t border-slate-200 pt-4">
              <summary className="cursor-pointer text-sm font-semibold text-slate-600">
                Opções do dataset
              </summary>
              <div className="mt-4 max-w-2xl space-y-4">
                <p className="text-sm leading-6 text-slate-600">
                  Regenerar substitui os arquivos CSV/XLSX e os pacientes de
                  origem padrão. Registros importados são preservados; IDs
                  conflitantes serão ignorados. A mesma seed e o mesmo tamanho
                  reproduzem os mesmos dados.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="field-label">
                    Quantidade de pacientes
                    <input
                      className="field"
                      type="number"
                      min={1}
                      max={10000}
                      value={size}
                      onChange={(event) => {
                        setSize(Number(event.target.value));
                        setConfirm(false);
                      }}
                    />
                  </label>
                  <label className="field-label">
                    Seed
                    <input
                      className="field"
                      type="number"
                      min={0}
                      max={2147483647}
                      value={seed}
                      onChange={(event) => {
                        setSeed(Number(event.target.value));
                        setConfirm(false);
                      }}
                    />
                  </label>
                </div>
                <label className="flex items-start gap-3 text-sm leading-6">
                  <input
                    type="checkbox"
                    className="mt-1 h-4 w-4"
                    checked={confirm}
                    onChange={(event) => setConfirm(event.target.checked)}
                  />
                  Confirmo a substituição do dataset padrão e de seus pacientes.
                </label>
                <button
                  className="btn-secondary"
                  disabled={
                    !confirm ||
                    busy ||
                    !Number.isInteger(size) ||
                    size < 1 ||
                    size > 10000 ||
                    !Number.isInteger(seed) ||
                    seed < 0 ||
                    seed > 2147483647
                  }
                  onClick={() => void regenerate()}
                >
                  {busy ? "Regenerando…" : "Regenerar dataset padrão"}
                </button>
                {regenError && <ErrorState message={regenError} />}
                {message && (
                  <p
                    role="status"
                    className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800"
                  >
                    {message}
                  </p>
                )}
              </div>
            </details>
          </section>
        </>
      )}
    </div>
  );
}
