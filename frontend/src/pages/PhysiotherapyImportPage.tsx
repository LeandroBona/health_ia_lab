import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, FileSpreadsheet, Upload } from "lucide-react";
import { ApiError, physiotherapyApi } from "../services/api";
import type {
  ImportResult,
  Preview,
  ValidationProblem,
} from "../types/physiotherapy";
import {
  columnLabels,
  PhysioHeader,
  number,
} from "../components/physiotherapy/shared";

export function PhysiotherapyImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [problem, setProblem] = useState<ValidationProblem | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [synthetic, setSynthetic] = useState(false);
  function select(fileValue?: File) {
    if (busy) return;
    setFile(fileValue ?? null);
    setPreview(null);
    setProblem(null);
    setResult(null);
    setSynthetic(false);
  }
  function report(err: unknown) {
    setProblem(
      err instanceof ApiError
        ? err.problem
        : {
            message:
              err instanceof Error
                ? err.message
                : "Falha de comunicação. Tente novamente.",
          },
    );
  }
  async function validate() {
    if (!file) return;
    setBusy(true);
    setProblem(null);
    setPreview(null);
    try {
      if (!/\.(csv|xlsx)$/i.test(file.name))
        throw new Error("Selecione um arquivo CSV ou XLSX.");
      if (file.size > 5 * 1024 * 1024)
        throw new Error("O limite por arquivo é de 5 MB.");
      setPreview(await physiotherapyApi.preview(file));
    } catch (err) {
      report(err);
    } finally {
      setBusy(false);
    }
  }
  async function confirm() {
    if (!preview) return;
    setBusy(true);
    setProblem(null);
    try {
      setResult(await physiotherapyApi.confirm(preview.token));
      setPreview(null);
    } catch (err) {
      report(err);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-6">
      <PhysioHeader
        back
        title="Importar planilha"
        description="Selecione o arquivo, revise a validação e confirme a importação dos pacientes sintéticos."
      />
      <ol
        className="flex flex-wrap gap-3 text-sm font-semibold text-slate-500"
        aria-label="Etapas da importação"
      >
        {["1. Selecionar", "2. Validar e revisar", "3. Confirmar e salvar"].map(
          (label, index) => (
            <li
              key={label}
              className={`rounded-full px-4 py-2 ${index === (result ? 2 : preview ? 1 : 0) ? "bg-ocean-100 text-ocean-900" : "bg-white"}`}
            >
              {label}
            </li>
          ),
        )}
      </ol>
      {result ? (
        <section className="surface-card p-7" role="status">
          <CheckCircle2 className="mb-4 text-emerald-700" size={34} />
          <h2 className="section-title">Importação concluída</h2>
          <div className="my-6 grid gap-4 sm:grid-cols-3">
            {[
              ["Importados", result.imported],
              ["Ignorados (duplicados)", result.ignored],
              ["Total", result.total],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-sm text-slate-500">{label}</p>
                <p className="mt-2 text-3xl font-bold">{value}</p>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-3">
            <Link className="btn-primary" to="/fisioterapia">
              Ver pacientes
            </Link>
            <button className="btn-secondary" onClick={() => select()}>
              Importar outro arquivo
            </button>
          </div>
        </section>
      ) : (
        <>
          <section className="surface-card p-5 sm:p-7">
            <h2 className="text-xl font-bold">Arquivo de pacientes</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              CSV em UTF-8 (vírgula ou ponto e vírgula) ou XLSX (primeira aba).
              Até 5 MB e 10.000 registros. Use as 18 colunas do modelo, sem
              informações pessoais. Valores numéricos devem ser inteiros.
            </p>
            <div className="my-3 flex flex-wrap gap-4 text-sm font-semibold text-ocean-700">
              <a href={physiotherapyApi.downloadUrl("csv")}>
                Baixar modelo CSV
              </a>
              <a href={physiotherapyApi.downloadUrl("xlsx")}>
                Baixar modelo XLSX
              </a>
            </div>
            <div
              className="mt-5 rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-6"
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                select(event.dataTransfer.files[0]);
              }}
            >
              <Upload className="mb-3 text-ocean-700" />
              <label className="field-label" htmlFor="dataset-file">
                Arraste um arquivo aqui ou selecione no computador
              </label>
              <input
                className="mt-3 block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-ocean-100 file:px-4 file:py-2 file:font-semibold file:text-ocean-900"
                id="dataset-file"
                type="file"
                accept=".csv,.xlsx"
                disabled={busy}
                onChange={(event) => select(event.target.files?.[0])}
              />
            </div>
            {file && (
              <div className="mt-4 flex items-start gap-3 rounded-xl border border-slate-200 p-4">
                <FileSpreadsheet className="shrink-0 text-ocean-700" />
                <div className="min-w-0">
                  <p className="break-all font-semibold">{file.name}</p>
                  <p className="mt-1 text-sm text-slate-500">
                    {number(file.size / 1024)} KB ·{" "}
                    {file.name.split(".").pop()?.toUpperCase()}
                  </p>
                </div>
              </div>
            )}
            <label className="mt-4 flex items-start gap-3 text-sm leading-6">
              <input
                type="checkbox"
                checked={synthetic}
                disabled={busy}
                className="mt-1 h-4 w-4"
                onChange={(event) => setSynthetic(event.target.checked)}
              />
              Confirmo que o arquivo contém apenas dados sintéticos e nenhum
              dado pessoal identificável.
            </label>
            <button
              className="btn-primary mt-4"
              disabled={!file || !synthetic || busy}
              onClick={() => void validate()}
            >
              {busy ? "Processando…" : "Validar dados"}
            </button>
          </section>
          {problem && (
            <section
              role="alert"
              className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-900"
            >
              <h2 className="text-lg font-bold">Confira os dados</h2>
              <p className="mt-2">{problem.message}</p>
              {!!problem.missing_columns?.length && (
                <p className="mt-3 break-words">
                  Colunas ausentes: {problem.missing_columns.join(", ")}
                </p>
              )}
              {!!problem.extra_columns?.length && (
                <p className="mt-3 break-words">
                  Colunas não permitidas: {problem.extra_columns.join(", ")}
                </p>
              )}
              {problem.invalid_rows !== undefined && (
                <p className="mt-3">
                  {problem.invalid_rows} linhas inválidas;{" "}
                  {problem.missing_total ?? 0} valores ausentes. Exibindo até
                  100 erros.
                </p>
              )}
              {problem.errors && (
                <ul className="mt-3 max-h-64 space-y-2 overflow-auto text-sm">
                  {problem.errors.map((error) => (
                    <li key={error.row}>
                      Linha {error.row}: {error.message}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
          {preview && (
            <section className="surface-card min-w-0 overflow-hidden">
              <div className="p-5 sm:p-7">
                <div className="flex items-center gap-2 text-emerald-800">
                  <CheckCircle2 />
                  <h2 className="text-xl font-bold">Planilha válida</h2>
                </div>
                <p className="mt-2 break-all text-sm text-slate-500">
                  {preview.filename}
                </p>
                <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  {[
                    ["Registros", preview.record_count],
                    ["Colunas", preview.column_count],
                    ["Dados ausentes", preview.missing_total],
                    ["Duplicados a ignorar", preview.duplicates],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">{label}</p>
                      <p className="mt-2 text-2xl font-bold">{value}</p>
                    </div>
                  ))}
                </div>
                <details className="mt-5">
                  <summary className="cursor-pointer font-semibold">
                    Colunas, tipos detectados e ausências
                  </summary>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                    {preview.columns.map((column) => (
                      <p
                        className="break-words rounded-lg bg-slate-50 p-3 text-sm"
                        key={column}
                      >
                        <strong>{column}</strong>
                        <br />
                        {preview.detected_types[column]} · ausentes:{" "}
                        {preview.missing_values[column]}
                      </p>
                    ))}
                  </div>
                </details>
                <h3 className="mt-6 font-bold">
                  Primeiros {preview.preview.length} registros
                </h3>
              </div>
              <div
                className="max-h-96 overflow-auto"
                tabIndex={0}
                aria-label="Prévia da planilha"
              >
                <table className="data-table">
                  <thead>
                    <tr>
                      {preview.columns.map((column) => (
                        <th key={column}>{columnLabels[column]}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview.map((patient, index) => (
                      <tr key={index}>
                        {preview.columns.map((column) => (
                          <td key={column}>{patient[column]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="space-y-4 p-5 sm:p-7">
                <p className="text-sm leading-6 text-slate-600">
                  {number(preview.importable)} registros disponíveis para
                  importação. IDs já existentes ou repetidos no arquivo serão
                  ignorados e contabilizados. A contagem é conferida novamente
                  ao salvar. A prévia expira em 30 minutos. Nenhum paciente foi
                  salvo ainda.
                </p>
                <button
                  className="btn-primary"
                  disabled={busy || !synthetic}
                  onClick={() => void confirm()}
                >
                  {busy ? "Importando…" : "Importar dados"}
                </button>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
