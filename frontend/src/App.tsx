import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./layouts/AppLayout";
import { modulePages } from "./data/modules";

const DashboardPage = lazy(() =>
  import("./pages/DashboardPage").then(({ DashboardPage }) => ({
    default: DashboardPage,
  })),
);
const ModulePage = lazy(() =>
  import("./pages/ModulePage").then(({ ModulePage }) => ({
    default: ModulePage,
  })),
);
const AboutPage = lazy(() =>
  import("./pages/AboutPage").then(({ AboutPage }) => ({ default: AboutPage })),
);
const PhysiotherapyPage = lazy(() =>
  import("./pages/PhysiotherapyPage").then((module) => ({
    default: module.PhysiotherapyPage,
  })),
);
const PhysiotherapyPatientPage = lazy(() =>
  import("./pages/PhysiotherapyPatientPage").then((module) => ({
    default: module.PhysiotherapyPatientPage,
  })),
);
const PhysiotherapyExplorePage = lazy(() =>
  import("./pages/PhysiotherapyExplorePage").then((module) => ({
    default: module.PhysiotherapyExplorePage,
  })),
);
const PhysiotherapyImportPage = lazy(() =>
  import("./pages/PhysiotherapyImportPage").then((module) => ({
    default: module.PhysiotherapyImportPage,
  })),
);
const PhysiotherapyModelPage = lazy(() =>
  import("./pages/PhysiotherapyModelPage").then((module) => ({
    default: module.PhysiotherapyModelPage,
  })),
);
const PhysiotherapyLabPage = lazy(() =>
  import("./pages/PhysiotherapyLabPage").then((module) => ({
    default: module.PhysiotherapyLabPage,
  })),
);
const PhysiotherapySimulatorPage = lazy(() =>
  import("./pages/PhysiotherapySimulatorPage").then((module) => ({
    default: module.PhysiotherapySimulatorPage,
  })),
);
const NursingPage = lazy(() => import("./pages/NursingPage").then(m => ({default:m.NursingPage})));
const NursingPatientPage = lazy(() => import("./pages/NursingPatientPage").then(m => ({default:m.NursingPatientPage})));
const NursingMeasurementPage = lazy(() => import("./pages/NursingMeasurementPage").then(m => ({default:m.NursingMeasurementPage})));
const NursingLabPage = lazy(() => import("./pages/NursingLabPage").then(m => ({default:m.NursingLabPage})));
const NursingModelPage = lazy(() => import("./pages/NursingModelPage").then(m => ({default:m.NursingModelPage})));
const NursingDatasetPage = lazy(() => import("./pages/NursingDatasetPage").then(m => ({default:m.NursingDatasetPage})));
const NursingTimelinePage = lazy(() => import("./pages/NursingTimelinePage").then(m => ({default:m.NursingTimelinePage})));
const NursingImportPage = lazy(() => import("./pages/NursingImportPage").then(m => ({default:m.NursingImportPage})));
const ModelsCatalogPage = lazy(() => import("./pages/ModelsCatalogPage").then(m => ({default:m.ModelsCatalogPage})));
const PharmacyPage = lazy(() => import("./pages/PharmacyPage").then(m => ({default:m.PharmacyPage})));
const PharmacyAdherencePage = lazy(() => import("./pages/PharmacyAdherencePage").then(m => ({default:m.PharmacyAdherencePage})));
const PharmacyAdherencePatientPage = lazy(() => import("./pages/PharmacyAdherencePatientPage").then(m => ({default:m.PharmacyAdherencePatientPage})));
const PharmacyAdherenceLabPage = lazy(() => import("./pages/PharmacyAdherenceLabPage").then(m => ({default:m.PharmacyAdherenceLabPage})));
const PharmacyAdherenceModelPage = lazy(() => import("./pages/PharmacyAdherenceModelPage").then(m => ({default:m.PharmacyAdherenceModelPage})));
const PharmacyDemandPage = lazy(() => import("./pages/PharmacyDemandPage").then(m => ({default:m.PharmacyDemandPage})));
const PharmacyDemandMedicationPage = lazy(() => import("./pages/PharmacyDemandMedicationPage").then(m => ({default:m.PharmacyDemandMedicationPage})));
const PharmacyDemandLabPage = lazy(() => import("./pages/PharmacyDemandLabPage").then(m => ({default:m.PharmacyDemandLabPage})));
const PharmacyDemandModelPage = lazy(() => import("./pages/PharmacyDemandModelPage").then(m => ({default:m.PharmacyDemandModelPage})));
const PharmacyImportPage = lazy(() => import("./pages/PharmacyImportPage").then(m => ({default:m.PharmacyImportPage})));
const VeterinaryPage = lazy(() => import("./pages/VeterinaryPage").then(m => ({default:m.VeterinaryPage})));
const VeterinaryAnimalPage = lazy(() => import("./pages/VeterinaryAnimalPage").then(m => ({default:m.VeterinaryAnimalPage})));
const VeterinaryLabPage = lazy(() => import("./pages/VeterinaryLabPage").then(m => ({default:m.VeterinaryLabPage})));
const VeterinaryModelPage = lazy(() => import("./pages/VeterinaryModelPage").then(m => ({default:m.VeterinaryModelPage})));
const VeterinaryImportPage = lazy(() => import("./pages/VeterinaryImportPage").then(m => ({default:m.VeterinaryImportPage})));
const PsychologyPage = lazy(() => import("./pages/PsychologyPage").then(m => ({default:m.PsychologyPage})));
const PsychologyRecordPage = lazy(() => import("./pages/PsychologyRecordPage").then(m => ({default:m.PsychologyRecordPage})));
const PsychologyLabPage = lazy(() => import("./pages/PsychologyLabPage").then(m => ({default:m.PsychologyLabPage})));
const PsychologyModelPage = lazy(() => import("./pages/PsychologyModelPage").then(m => ({default:m.PsychologyModelPage})));
const PsychologyImportPage = lazy(() => import("./pages/PsychologyImportPage").then(m => ({default:m.PsychologyImportPage})));
const VisionPage = lazy(() => import("./pages/VisionPage").then(m => ({default:m.VisionPage})));
const VisionLabPage = lazy(() => import("./pages/VisionLabPage").then(m => ({default:m.VisionLabPage})));
const GenerativePage = lazy(() => import("./pages/GenerativePage").then(m => ({default:m.GenerativePage})));
const HowItWorksPage = lazy(() => import("./pages/HowItWorksPage").then(m => ({default:m.HowItWorksPage})));
const GeneralLabPage = lazy(() => import("./pages/GeneralLabPage").then(m => ({default:m.GeneralLabPage})));
const DatasetsCatalogPage = lazy(() => import("./pages/DatasetsCatalogPage").then(m => ({default:m.DatasetsCatalogPage})));
const DatasetDetailPage = lazy(() => import("./pages/DatasetDetailPage").then(m => ({default:m.DatasetDetailPage})));
const HistoryPage = lazy(() => import("./pages/HistoryPage").then(m => ({default:m.HistoryPage})));
const HistoryDetailPage = lazy(() => import("./pages/HistoryDetailPage").then(m => ({default:m.HistoryDetailPage})));
const SystemPage = lazy(() => import("./pages/SystemPage").then(m => ({default:m.SystemPage})));
const ClassroomPage = lazy(() => import("./pages/ClassroomPage").then(m => ({default:m.ClassroomPage})));
const ClassroomGlossaryPage = lazy(() => import("./pages/ClassroomGlossaryPage").then(m => ({default:m.ClassroomGlossaryPage})));

function PageLoader() {
  return (
    <div
      className="surface-card grid min-h-64 place-items-center"
      role="status"
    >
      <div className="text-center">
        <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-slate-200 border-t-ocean-600" />
        <p className="mt-4 text-sm font-semibold text-slate-600">
          Carregando módulo...
        </p>
      </div>
    </div>
  );
}

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="aula" element={<ClassroomPage />} />
        <Route path="aula/glossario" element={<ClassroomGlossaryPage />} />
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="laboratorio" element={<GeneralLabPage />} />
          <Route path="como-funciona" element={<HowItWorksPage />} />
          <Route path="datasets" element={<DatasetsCatalogPage />} />
          <Route path="datasets/:datasetId" element={<DatasetDetailPage />} />
          <Route path="historico" element={<HistoryPage />} />
          <Route path="historico/:historyId" element={<HistoryDetailPage />} />
          <Route path="sistema" element={<SystemPage />} />
          <Route path="fisioterapia" element={<PhysiotherapyPage />} />
          <Route
            path="fisioterapia/paciente/:patientId"
            element={<PhysiotherapyPatientPage />}
          />
          <Route path="fisioterapia/pacientes/:patientId" element={<PhysiotherapyPatientPage />} />
          <Route
            path="fisioterapia/explorar"
            element={<PhysiotherapyExplorePage />}
          />
          <Route
            path="fisioterapia/importar"
            element={<PhysiotherapyImportPage />}
          />
          <Route
            path="fisioterapia/modelo"
            element={<PhysiotherapyModelPage />}
          />
          <Route
            path="fisioterapia/laboratorio"
            element={<PhysiotherapyLabPage />}
          />
          <Route
            path="fisioterapia/simulador"
            element={<PhysiotherapySimulatorPage />}
          />
          <Route path="enfermagem" element={<NursingPage />} />
          <Route path="enfermagem/paciente/:patientId" element={<NursingPatientPage />} />
          <Route path="enfermagem/medicao/:measurementId" element={<NursingMeasurementPage />} />
          <Route path="enfermagem/laboratorio" element={<NursingLabPage />} />
          <Route path="enfermagem/modelo" element={<NursingModelPage />} />
          <Route path="enfermagem/dataset" element={<NursingDatasetPage />} />
          <Route path="enfermagem/dataset/temporal" element={<NursingTimelinePage />} />
          <Route path="enfermagem/importar" element={<NursingImportPage />} />
          <Route path="farmacia" element={<PharmacyPage />} />
          <Route path="farmacia/adesao" element={<PharmacyAdherencePage />} />
          <Route path="farmacia/adesao/paciente/:patientId" element={<PharmacyAdherencePatientPage />} />
          <Route path="farmacia/adesao/laboratorio" element={<PharmacyAdherenceLabPage />} />
          <Route path="farmacia/adesao/modelo" element={<PharmacyAdherenceModelPage />} />
          <Route path="farmacia/demanda" element={<PharmacyDemandPage />} />
          <Route path="farmacia/demanda/laboratorio" element={<PharmacyDemandLabPage />} />
          <Route path="farmacia/demanda/modelo" element={<PharmacyDemandModelPage />} />
          <Route path="farmacia/demanda/:medicationId" element={<PharmacyDemandMedicationPage />} />
          <Route path="farmacia/:kind/importar" element={<PharmacyImportPage />} />
          <Route path="veterinaria" element={<VeterinaryPage />} />
          <Route path="veterinaria/animal/:animalId" element={<VeterinaryAnimalPage />} />
          <Route path="veterinaria/laboratorio" element={<VeterinaryLabPage />} />
          <Route path="veterinaria/modelo" element={<VeterinaryModelPage />} />
          <Route path="veterinaria/importar" element={<VeterinaryImportPage />} />
          <Route path="psicologia" element={<PsychologyPage />} />
          <Route path="psicologia/relato/:recordId" element={<PsychologyRecordPage />} />
          <Route path="psicologia/laboratorio" element={<PsychologyLabPage />} />
          <Route path="psicologia/modelo" element={<PsychologyModelPage />} />
          <Route path="psicologia/importar" element={<PsychologyImportPage />} />
          <Route path="visao-computacional" element={<VisionPage />} />
          <Route path="visao-computacional/laboratorio" element={<VisionLabPage />} />
          <Route path="ia-generativa" element={<GenerativePage />} />
          <Route path="modelos-de-ia" element={<ModelsCatalogPage />} />
          <Route path="modelos" element={<ModelsCatalogPage />} />
          {modulePages
            .filter((module) => !["fisioterapia", "enfermagem", "farmacia", "veterinaria", "psicologia", "visao-computacional", "ia-generativa", "datasets", "modelos-de-ia"].includes(module.path))
            .map((module) => (
              <Route
                key={module.path}
                path={module.path}
                element={<ModulePage module={module} />}
              />
            ))}
          <Route path="sobre" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
