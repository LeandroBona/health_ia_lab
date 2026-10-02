import type { LucideIcon } from "lucide-react";
import {
  Bot,
  BrainCircuit,
  Database,
  Dna,
  HeartPulse,
  Microscope,
  Pill,
  ScanLine,
  ShieldPlus,
  Sparkles,
  Stethoscope,
} from "lucide-react";

export interface ModuleDefinition {
  path: string;
  title: string;
  shortDescription: string;
  description: string;
  futureAi: string;
  concepts: string[];
  icon: LucideIcon;
  accent: string;
  courseArea?: boolean;
}

export const courseModules: ModuleDefinition[] = [
  {
    path: "fisioterapia",
    title: "Fisioterapia",
    shortDescription: "Análise de movimento, evolução funcional e apoio à reabilitação.",
    description:
      "Explorará como dados de movimento e evolução funcional podem apoiar estudos sobre reabilitação.",
    futureAi: "Machine Learning, análise preditiva e visão computacional",
    concepts: ["Movimento", "Evolução funcional", "Classificação"],
    icon: HeartPulse,
    accent: "bg-cyan-50 text-cyan-700",
    courseArea: true,
  },
  {
    path: "enfermagem",
    title: "Enfermagem",
    shortDescription: "Monitoramento de sinais e reconhecimento de alterações em séries temporais.",
    description:
      "Apresentará o uso responsável de sinais sintéticos para estudar padrões e mudanças ao longo do tempo.",
    futureAi: "Detecção de anomalias e análise de dados temporais",
    concepts: ["Sinais vitais", "Séries temporais", "Anomalias"],
    icon: ShieldPlus,
    accent: "bg-blue-50 text-blue-700",
    courseArea: true,
  },
  {
    path: "farmacia",
    title: "Farmácia",
    shortDescription: "Previsão de demanda e exploração de padrões em dados farmacêuticos.",
    description:
      "Demonstrará como variáveis sintéticas podem ser organizadas para exercícios de previsão e planejamento.",
    futureAi: "Modelos preditivos e previsão de demanda",
    concepts: ["Demanda", "Estoque", "Regressão"],
    icon: Pill,
    accent: "bg-violet-50 text-violet-700",
    courseArea: true,
  },
  {
    path: "veterinaria",
    title: "Veterinária",
    shortDescription: "Classificação e detecção de anomalias em acompanhamento de animais fictícios.",
    description:
      "Trabalhará a leitura de indicadores sintéticos para estudar evolução, agrupamentos e classificação.",
    futureAi: "Machine Learning + Detecção de Anomalias · Disponível",
    concepts: ["Evolução", "Anomalias", "Classificação"],
    icon: Dna,
    accent: "bg-amber-50 text-amber-700",
    courseArea: true,
  },
  {
    path: "psicologia",
    title: "Psicologia",
    shortDescription: "NLP, classificação, similaridade e agrupamento de relatos sintéticos.",
    description:
      "Demonstra TF-IDF, classificação temática, similaridade e clustering de relatos fictícios.",
    futureAi: "Processamento de Linguagem Natural · Disponível",
    concepts: ["Texto sintético", "Classificação textual", "Clustering"],
    icon: BrainCircuit,
    accent: "bg-rose-50 text-rose-700",
    courseArea: true,
  },
];

export const technologyModules: ModuleDefinition[] = [
  {
    path: "visao-computacional",
    title: "Visão Computacional",
    shortDescription: "Estimativa de pose pela webcam e métricas matemáticas de movimento.",
    description:
      "Demonstra landmarks corporais, ângulos, comparação entre lados e contagem de movimentos no navegador.",
    futureAi: "Pose Landmarker · Disponível",
    concepts: ["Webcam", "Landmarks", "Geometria"],
    icon: ScanLine,
    accent: "bg-sky-50 text-sky-700",
  },
  {
    path: "ia-generativa",
    title: "IA Generativa",
    shortDescription: "Explicações textuais, prompts estruturados e conteúdo educacional.",
    description:
      "Demonstra uma camada opcional de comunicação para resultados produzidos pelos modelos especializados.",
    futureAi: "Geração textual + templates locais · Disponível",
    concepts: ["Prompts", "Explicações", "Modo local"],
    icon: Sparkles,
    accent: "bg-fuchsia-50 text-fuchsia-700",
  },
  {
    path: "datasets",
    title: "Datasets",
    shortDescription: "Organização, qualidade e documentação de dados sintéticos.",
    description:
      "Concentrará conjuntos de dados sintéticos e materiais sobre preparação, qualidade e documentação.",
    futureAi: "Análise exploratória e preparação de dados",
    concepts: ["Dados sintéticos", "Qualidade", "Dicionário de dados"],
    icon: Database,
    accent: "bg-emerald-50 text-emerald-700",
  },
  {
    path: "modelos-de-ia",
    title: "Modelos de IA",
    shortDescription: "Catálogo futuro de experimentos, métricas e versões.",
    description:
      "Organizará modelos educacionais, objetivos dos experimentos e métricas de avaliação.",
    futureAi: "Classificação, regressão e avaliação de modelos",
    concepts: ["Experimentos", "Métricas", "Versionamento"],
    icon: Bot,
    accent: "bg-indigo-50 text-indigo-700",
  },
];

export const modulePages = [...courseModules, ...technologyModules];

export const extraMenuItems = [
  {
    path: "sobre",
    title: "Sobre",
    icon: Microscope,
  },
];

export const applicationChartData = [
  { area: "Fisioterapia", abordagens: 3 },
  { area: "Enfermagem", abordagens: 2 },
  { area: "Farmácia", abordagens: 2 },
  { area: "Veterinária", abordagens: 2 },
  { area: "Psicologia", abordagens: 1 },
];

export const dashboardIcon = Stethoscope;
