import { useEffect, useState } from "react";
import { physiotherapyApi } from "../services/api";
import type { DatasetSchema, Exploration } from "../types/physiotherapy";
import {
  columnLabels,
  ErrorState,
  LoadingState,
  number,
  PhysioHeader,
} from "../components/physiotherapy/shared";
import { DistributionChart } from "../components/physiotherapy/Charts";

export function PhysiotherapyExplorePage() {
  const [schema, setSchema] = useState<DatasetSchema | null>(null);
  const [column, setColumn] = useState("idade");
  const [data, setData] = useState<Exploration | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setData(null);
    setError("");
    Promise.all([physiotherapyApi.schema(), physiotherapyApi.explore(column)])
      .then(([schemaValue, value]) => {
        if (active) {
          setSchema(schemaValue);
          setData(value);
        }
      })
      .catch((err: unknown) => {
        if (active)
          setError(err instanceof Error ? err.message : "Falha na exploração.");
      });
    return () => {
      active = false;
    };
  }, [column]);
  return (
    <div className="space-y-6">
      <PhysioHeader
        back
        title="Explorar Dataset"
        description="Estatísticas descritivas dos pacientes de Fisioterapia armazenados no laboratório."
      />
      <aside className="rounded-2xl bg-ink p-6 text-white">
        <h2 className="text-xl font-bold">
          Antes de treinar uma Inteligência Artificial, precisamos conhecer os
          dados.
        </h2>
        <div className="mt-4 grid gap-4 text-sm leading-6 text-slate-300 md:grid-cols-3">
          <p>
            <strong className="text-ocean-200">Qualidade e ausências.</strong>{" "}
            Tipos, faixas e campos completos tornam os dados consistentes.
          </p>
          <p>
            <strong className="text-ocean-200">Distribuição e outliers.</strong>{" "}
            Observe concentrações e valores distantes dos demais; eles não são
            necessariamente erros.
          </p>
          <p>
            <strong className="text-ocean-200">Tipos de variáveis.</strong>{" "}
            Numéricas têm medidas; categóricas descrevem grupos. IDs apenas
            identificam registros.
          </p>
        </div>
      </aside>
      <label className="field-label max-w-lg">
        Selecione uma coluna
        <select
          className="field mt-2"
          value={column}
          onChange={(event) => setColumn(event.target.value)}
        >
          {schema ? (
            schema.columns.map((key) => (
              <option value={key} key={key}>
                {columnLabels[key]} ({key})
              </option>
            ))
          ) : (
            <option value="idade">Idade</option>
          )}
        </select>
      </label>
      {error ? (
        <ErrorState message={error} />
      ) : !data ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <Stat label="Valores presentes" value={data.count} />
            <Stat label="Dados ausentes" value={data.missing} />
            <Stat label="Valores distintos" value={data.unique} />
          </div>
          {data.kind === "numeric" && (
            <>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                {(["mean", "min", "max", "median", "std"] as const).map(
                  (key, index) => (
                    <Stat
                      key={key}
                      label={
                        [
                          "Média",
                          "Mínimo",
                          "Máximo",
                          "Mediana",
                          "Desvio padrão",
                        ][index]
                      }
                      value={data[key]}
                    />
                  ),
                )}
              </div>
              <p className="text-sm text-slate-500">
                Desvio padrão populacional. Faixas do histograma incluem o
                limite superior; a primeira também inclui o mínimo.
              </p>
            </>
          )}
          <DistributionChart
            title={
              data.kind === "numeric"
                ? "Distribuição dos valores"
                : "Quantidade por categoria"
            }
            data={data.distribution}
            horizontal
            description={columnLabels[data.column]}
          />
          {data.truncated && (
            <p className="text-sm text-slate-600">
              Exibindo as primeiras 30 categorias em ordem alfabética, de{" "}
              {number(data.unique)}. Identificadores possuem alta cardinalidade.
            </p>
          )}
        </>
      )}
    </div>
  );
}
function Stat({
  label,
  value,
}: {
  label: string;
  value: number | null | undefined;
}) {
  return (
    <article className="surface-card p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold">{number(value)}</p>
    </article>
  );
}
