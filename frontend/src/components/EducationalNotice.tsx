import { Info } from "lucide-react";

interface EducationalNoticeProps {
  emphasis?: boolean;
}

export function EducationalNotice({ emphasis = false }: EducationalNoticeProps) {
  return (
    <div
      className={
        emphasis
          ? "rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-amber-950"
          : "border-b border-slate-200 bg-white/90 px-4 py-3 text-slate-700 backdrop-blur sm:px-6 lg:px-8"
      }
      role="note"
    >
      <div className="mx-auto flex max-w-[1500px] items-start gap-3">
        <Info className="mt-0.5 shrink-0 text-amber-600" aria-hidden="true" size={19} />
        <p className="text-sm font-medium leading-6">
          Ambiente educacional desenvolvido exclusivamente com dados sintéticos. Os resultados apresentados não
          representam diagnóstico, tratamento ou recomendação clínica.
        </p>
      </div>
    </div>
  );
}

