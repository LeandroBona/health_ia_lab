import { useEffect, useState } from "react";
import { physiotherapyApi } from "../services/api";
import type { DatasetSchema } from "../types/physiotherapy";
import { ManualPrediction } from "../components/physiotherapy/ManualPrediction";
import {
  ErrorState,
  LoadingState,
  PhysioHeader,
} from "../components/physiotherapy/shared";
import { ModelNotice } from "../components/physiotherapy/PredictionPanel";

export function PhysiotherapyLabPage() {
  const [schema, setSchema] = useState<DatasetSchema | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    physiotherapyApi
      .schema()
      .then(setSchema)
      .catch((err: unknown) =>
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar o formulário.",
        ),
      );
  }, []);
  return (
    <div className="space-y-6">
      <PhysioHeader
        back
        title="Laboratório de previsão"
        description="Monte um registro sintético, classifique e peça uma explicação individual sem salvar dados."
      />
      <ModelNotice />
      {error && <ErrorState message={error} />}
      {!schema && !error && <LoadingState />}
      {schema && <ManualPrediction schema={schema} />}
    </div>
  );
}
