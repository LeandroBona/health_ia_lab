import { ArrowLeft, Info } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import type { ReactNode } from "react";
import type { Patient, Result } from "../../types/physiotherapy";

export const resultLabels: Record<Result, string> = {
  recuperacao_adequada: "Recuperação adequada",
  recuperacao_lenta: "Recuperação lenta",
  abandono: "Abandono",
};
const resultStyles: Record<Result, string> = {
  recuperacao_adequada: "bg-emerald-50 text-emerald-800 border-emerald-200",
  recuperacao_lenta: "bg-amber-50 text-amber-900 border-amber-200",
  abandono: "bg-rose-50 text-rose-800 border-rose-200",
};
export const columnLabels: Record<keyof Patient, string> = {
  patient_id: "Paciente",
  idade: "Idade",
  sexo: "Sexo",
  tipo_lesao: "Tipo de lesão",
  tempo_lesao_dias: "Tempo da lesão (dias)",
  dor_inicial: "Dor inicial",
  dor_atual: "Dor atual",
  mobilidade_inicial: "Mobilidade inicial",
  mobilidade_atual: "Mobilidade atual",
  forca_muscular: "Força muscular",
  sessoes_previstas: "Sessões previstas",
  sessoes_realizadas: "Sessões realizadas",
  faltas: "Faltas",
  adesao_exercicios: "Adesão aos exercícios",
  comorbidades: "Comorbidades",
  indice_funcional_inicial: "Índice funcional inicial",
  indice_funcional_atual: "Índice funcional atual",
  resultado: "Resultado",
};
export const number = (value: number | null | undefined) =>
  value == null
    ? "—"
    : new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(
        value,
      );

export function ResultBadge({ result }: { result: Result }) {
  return (
    <span
      className={`inline-flex whitespace-nowrap rounded-full border px-2.5 py-1 text-sm font-semibold ${resultStyles[result]}`}
    >
      {resultLabels[result]}
    </span>
  );
}
export function SyntheticNotice() {
  return (
    <>
      <nav aria-label="Seções de Fisioterapia" className="flex flex-wrap gap-2">
        {[
          ["/fisioterapia", "Pacientes e dados"],
          ["/fisioterapia/explorar", "Explorar Dataset"],
          ["/fisioterapia/modelo", "Modelo de IA"],
          ["/fisioterapia/laboratorio", "Laboratório"],
          ["/fisioterapia/simulador", "Simulador"],
          ["/fisioterapia/importar", "Importar planilha"],
        ].map(([path, title]) => (
          <NavLink
            end
            key={path}
            to={path}
            className={({ isActive }) =>
              `rounded-xl px-4 py-2.5 text-sm font-semibold ${isActive ? "bg-ink text-white" : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`
            }
          >
            {title}
          </NavLink>
        ))}
      </nav>
      <p className="flex items-start gap-2 rounded-xl border border-ocean-200 bg-ocean-50 px-4 py-3 text-sm leading-6 text-ocean-900">
        <Info size={18} className="mt-1 shrink-0" />
        Os dados apresentados são sintéticos e não representam pacientes reais.
      </p>
    </>
  );
}
export function PhysioHeader({
  title,
  description,
  children,
  back = false,
}: {
  title: string;
  description: string;
  children?: ReactNode;
  back?: boolean;
}) {
  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-3xl">
          {back && (
            <Link
              className="mb-4 flex items-center gap-2 text-sm font-semibold text-ocean-700"
              to="/fisioterapia"
            >
              <ArrowLeft size={17} />
              Fisioterapia
            </Link>
          )}
          <p className="section-kicker">Laboratório de dados · Fisioterapia</p>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            {title}
          </h1>
          <p className="mt-3 text-base leading-7 text-slate-600">
            {description}
          </p>
        </div>
        {children}
      </div>
      <SyntheticNotice />
    </>
  );
}
export function LoadingState() {
  return (
    <div role="status" className="surface-card p-8 text-slate-600">
      Carregando dados de Fisioterapia…
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-rose-900"
    >
      <p>{message}</p>
      {retry && (
        <button className="btn-secondary mt-3" onClick={retry}>
          Tentar novamente
        </button>
      )}
    </div>
  );
}
export function Progress({
  value,
  max = 100,
  label,
}: {
  value: number;
  max?: number;
  label: string;
}) {
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      className="h-2.5 overflow-hidden rounded-full bg-slate-100"
    >
      <div
        className="h-full rounded-full bg-ocean-600"
        style={{ width: `${Math.min(100, (value / max) * 100)}%` }}
      />
    </div>
  );
}
