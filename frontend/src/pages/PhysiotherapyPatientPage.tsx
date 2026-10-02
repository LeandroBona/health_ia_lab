import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { physiotherapyApi } from "../services/api";
import type { Patient } from "../types/physiotherapy";
import {
  ErrorState,
  LoadingState,
  PhysioHeader,
  Progress,
  ResultBadge,
} from "../components/physiotherapy/shared";
import { PatientPrediction } from "../components/physiotherapy/PredictionPanel";

function Comparison({
  label,
  initial,
  current,
  max,
}: {
  label: string;
  initial: number;
  current: number;
  max: number;
}) {
  const difference = current - initial;
  return (
    <article className="surface-card p-6">
      <h3 className="text-lg font-bold">{label}</h3>
      <div className="mt-5 grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-slate-500">Inicial</p>
          <p className="my-2 text-2xl font-bold">
            {initial}
            <span className="text-sm font-normal text-slate-500">/{max}</span>
          </p>
          <Progress value={initial} max={max} label={`${label} inicial`} />
        </div>
        <div>
          <p className="text-sm text-slate-500">Atual</p>
          <p className="my-2 text-2xl font-bold">
            {current}
            <span className="text-sm font-normal text-slate-500">/{max}</span>
          </p>
          <Progress value={current} max={max} label={`${label} atual`} />
        </div>
      </div>
      <p className="mt-5 rounded-xl bg-slate-50 px-3 py-2 text-sm">
        Diferença:{" "}
        <strong>
          {difference > 0 ? "+" : ""}
          {difference}
        </strong>{" "}
        pontos (atual − inicial)
      </p>
    </article>
  );
}
export function PhysiotherapyPatientPage() {
  const { patientId = "" } = useParams();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setPatient(null);
    setError("");
    physiotherapyApi
      .patient(patientId)
      .then((value) => {
        if (active) setPatient(value);
      })
      .catch((err: unknown) => {
        if (active)
          setError(
            err instanceof Error ? err.message : "Paciente indisponível.",
          );
      });
    return () => {
      active = false;
    };
  }, [patientId]);
  return (
    <div className="space-y-6">
      <PhysioHeader
        back
        title={patientId}
        description="Ficha descritiva do paciente fictício. Comparação dos valores iniciais e atuais registrados."
      />
      {error ? (
        <ErrorState message={error} />
      ) : !patient ? (
        <LoadingState />
      ) : (
        <>
          <section className="surface-card p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="section-title">Dados do paciente</h2>
              <ResultBadge result={patient.resultado} />
            </div>
            <dl className="mt-6 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["Identificador", patient.patient_id],
                ["Idade", `${patient.idade} anos`],
                ["Sexo", patient.sexo],
                ["Tipo de lesão", patient.tipo_lesao],
                ["Tempo da lesão", `${patient.tempo_lesao_dias} dias`],
                ["Sessões previstas", patient.sessoes_previstas],
                ["Sessões realizadas", patient.sessoes_realizadas],
                ["Faltas", patient.faltas],
                ["Adesão", `${patient.adesao_exercicios}%`],
                ["Comorbidades", patient.comorbidades],
                ["Força muscular", `${patient.forca_muscular}/5`],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt className="text-sm text-slate-500">{label}</dt>
                  <dd className="mt-1 text-lg font-semibold">{value}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section>
            <h2 className="section-title">Evolução dos indicadores</h2>
            <p className="mb-5 mt-2 text-sm leading-6 text-slate-600">
              Dois momentos registrados; não há série temporal, diagnóstico ou
              recomendação. As diferenças são apenas aritméticas.
            </p>
            <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
              <Comparison
                label="Dor"
                initial={patient.dor_inicial}
                current={patient.dor_atual}
                max={10}
              />
              <Comparison
                label="Mobilidade"
                initial={patient.mobilidade_inicial}
                current={patient.mobilidade_atual}
                max={100}
              />
              <Comparison
                label="Índice funcional"
                initial={patient.indice_funcional_inicial}
                current={patient.indice_funcional_atual}
                max={100}
              />
              <article className="surface-card p-6">
                <h3 className="text-lg font-bold">Sessões</h3>
                <p className="my-5 text-3xl font-bold">
                  {patient.sessoes_realizadas} / {patient.sessoes_previstas}
                </p>
                <Progress
                  value={patient.sessoes_realizadas}
                  max={patient.sessoes_previstas}
                  label="Sessões realizadas"
                />
                <p className="mt-4 text-sm text-slate-600">
                  Faltas registradas: <strong>{patient.faltas}</strong>
                </p>
              </article>
              <article className="surface-card p-6">
                <h3 className="text-lg font-bold">Adesão aos exercícios</h3>
                <p className="my-5 text-3xl font-bold">
                  {patient.adesao_exercicios}%
                </p>
                <Progress
                  value={patient.adesao_exercicios}
                  label="Adesão aos exercícios"
                />
                <p className="mt-4 text-sm text-slate-600">
                  Percentual registrado no dataset.
                </p>
              </article>
            </div>
          </section>
          <PatientPrediction
            key={patient.patient_id}
            patientId={patient.patient_id}
          />
        </>
      )}
    </div>
  );
}
