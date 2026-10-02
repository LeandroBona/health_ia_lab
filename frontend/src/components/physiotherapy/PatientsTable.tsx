import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { physiotherapyApi } from "../../services/api";
import type { DatasetSchema, PatientsPage } from "../../types/physiotherapy";
import { ErrorState, ResultBadge, number, resultLabels } from "./shared";

export function PatientsTable({
  schema,
  revision,
}: {
  schema: DatasetSchema;
  revision: number;
}) {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<PatientsPage | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(params.get("search") ?? "");
  const page = Math.max(1, Number(params.get("page")) || 1);
  const query = params.toString();
  useEffect(() => {
    setSearch(params.get("search") ?? "");
  }, [query]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const request = new URLSearchParams(query);
    request.set("page", String(page));
    if (!request.has("page_size")) request.set("page_size", "20");
    physiotherapyApi
      .patients(request, controller.signal)
      .then(setData)
      .catch((err: unknown) => {
        if (!controller.signal.aborted)
          setError(
            err instanceof Error ? err.message : "Falha ao carregar pacientes.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, revision, page]);
  function filter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.set("page", "1");
    setParams(next);
  }
  function go(nextPage: number) {
    const next = new URLSearchParams(params);
    next.set("page", String(nextPage));
    setParams(next);
  }
  return (
    <section
      className="surface-card overflow-hidden"
      aria-labelledby="patients-title"
    >
      <div className="p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 id="patients-title" className="section-title">
              Pacientes
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {data
                ? `${number(data.total)} registros encontrados`
                : "Consultando registros"}{" "}
              · filtros aplicados à tabela
            </p>
          </div>
          <button
            className="btn-secondary"
            onClick={() => {
              setSearch("");
              setParams({});
            }}
          >
            Limpar filtros
          </button>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              filter("search", search);
            }}
          >
            <label className="field-label" htmlFor="patient-search">
              Buscar paciente
            </label>
            <div className="flex gap-2">
              <input
                className="field min-w-0"
                id="patient-search"
                placeholder="PAC-0001"
                maxLength={40}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <button className="btn-secondary" type="submit">
                Buscar
              </button>
            </div>
          </form>
          <label className="field-label">
            Tipo de lesão
            <select
              className="field mt-1"
              value={params.get("tipo_lesao") ?? ""}
              onChange={(event) => filter("tipo_lesao", event.target.value)}
            >
              <option value="">Todas as lesões</option>
              {schema.injuries.map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
          <label className="field-label">
            Sexo
            <select
              className="field mt-1"
              value={params.get("sexo") ?? ""}
              onChange={(event) => filter("sexo", event.target.value)}
            >
              <option value="">Todos</option>
              {schema.sexes.map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
          <label className="field-label">
            Resultado
            <select
              className="field mt-1"
              value={params.get("resultado") ?? ""}
              onChange={(event) => filter("resultado", event.target.value)}
            >
              <option value="">Todos os resultados</option>
              {schema.results.map((value) => (
                <option key={value} value={value}>
                  {resultLabels[value]}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
      {error ? (
        <div className="p-5">
          <ErrorState message={error} />
        </div>
      ) : (
        <>
          <div
            className="overflow-x-auto"
            tabIndex={0}
            aria-label="Tabela de pacientes, role horizontalmente para ver todas as colunas"
          >
            <table className="data-table">
              <thead>
                <tr>
                  {[
                    "Paciente",
                    "Idade",
                    "Lesão",
                    "Dor inicial",
                    "Dor atual",
                    "Adesão",
                    "Sessões",
                    "Faltas",
                    "Índice funcional atual",
                    "Resultado",
                    "Ações",
                  ].map((label) => (
                    <th key={label}>{label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={11} className="text-center" role="status">
                      Carregando pacientes…
                    </td>
                  </tr>
                ) : !data?.items.length ? (
                  <tr>
                    <td colSpan={11} className="text-center">
                      Nenhum paciente encontrado. Ajuste os filtros.
                    </td>
                  </tr>
                ) : (
                  data.items.map((patient) => (
                    <tr key={patient.patient_id}>
                      <td className="font-mono font-bold text-ocean-800">
                        {patient.patient_id}
                      </td>
                      <td>{patient.idade}</td>
                      <td>{patient.tipo_lesao}</td>
                      <td>{patient.dor_inicial}/10</td>
                      <td>{patient.dor_atual}/10</td>
                      <td>{patient.adesao_exercicios}%</td>
                      <td>
                        {patient.sessoes_realizadas}/{patient.sessoes_previstas}
                      </td>
                      <td>{patient.faltas}</td>
                      <td>{patient.indice_funcional_atual}/100</td>
                      <td>
                        <ResultBadge result={patient.resultado} />
                      </td>
                      <td>
                        <Link
                          className="font-bold text-ocean-700 hover:underline"
                          to={`/fisioterapia/paciente/${patient.patient_id}`}
                        >
                          Ver paciente
                          <span className="sr-only"> {patient.patient_id}</span>
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 px-5 py-4">
            <label className="flex items-center gap-2 text-sm">
              Por página
              <select
                className="field w-auto"
                value={params.get("page_size") ?? "20"}
                onChange={(event) => filter("page_size", event.target.value)}
              >
                {[10, 20, 50, 100].map((size) => (
                  <option key={size}>{size}</option>
                ))}
              </select>
            </label>
            <div className="flex items-center gap-3">
              <button
                className="btn-secondary"
                disabled={loading || page <= 1}
                onClick={() => go(page - 1)}
              >
                Anterior
              </button>
              <span className="text-sm">
                {page} / {data?.total_pages || 1}
              </span>
              <button
                className="btn-secondary"
                disabled={loading || page >= (data?.total_pages ?? 1)}
                onClick={() => go(page + 1)}
              >
                Próxima
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
