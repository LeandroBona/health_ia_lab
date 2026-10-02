import type { Patient } from "./physiotherapy";
import type { Prediction, PredictionExplanation, SimulationResult } from "./physiotherapyMl";
import type { AnomalyPrediction } from "./nursing";
import type { AdherencePrediction, DemandPrediction } from "./pharmacy";
import type { VetPrediction } from "./veterinary";
import type { PsychologyAnalysis } from "./psychology";
import type { GeneratedText } from "./generative";
import type { DemoScenarios } from "../services/demoScenarioService";

export interface ClassroomData {
  scenarios?:DemoScenarios;
  patient?:Patient;
  prediction?:Prediction;
  explanation?:PredictionExplanation;
  simulation?:SimulationResult;
  nursing?:AnomalyPrediction;
  nursingReference?:string;
  pharmacyAdherence?:AdherencePrediction;
  pharmacyDemand?:DemandPrediction;
  veterinary?:VetPrediction;
  psychology?:PsychologyAnalysis;
  nlpText?:string;
  psychologySimilar?:PsychologyAnalysis["similar"];
  generative?:GeneratedText;
}
