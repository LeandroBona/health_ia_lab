import assert from "node:assert/strict";
import test from "node:test";
import { classroomSteps } from "../src/data/classroomSteps.ts";
import { classroomGlossary, glossaryByTerm } from "../src/data/classroomGlossary.ts";

test("Modo Aula inicia do zero, organiza conceitos antes das demonstrações e mantém notas", () => {
  assert.ok(classroomSteps.length >= 33);
  assert.equal(new Set(classroomSteps.map(step => step.id)).size, classroomSteps.length);
  assert.equal(classroomSteps[0].id, "before");
  assert.equal(classroomSteps.at(-1).id, "closing");
  assert.ok(classroomSteps.findIndex(step=>step.id==="data") < classroomSteps.findIndex(step=>step.id==="physiotherapy"));
  assert.ok(classroomSteps.findIndex(step=>step.id==="nlp") < classroomSteps.findIndex(step=>step.id==="psychology"));
  assert.ok(classroomSteps.findIndex(step=>step.id==="visionConcept") < classroomSteps.findIndex(step=>step.id==="vision"));
  assert.ok(classroomSteps.findIndex(step=>step.id==="generativeConcept") < classroomSteps.findIndex(step=>step.id==="generative"));
  for (const step of classroomSteps) {
    assert.ok(step.title.length > 3);
    assert.ok(step.teacherNotes.length > 12);
    assert.ok(step.section.length > 2);
  }
});

test("glossário cobre os principais termos com linguagem simples", () => {
  assert.ok(classroomGlossary.length >= 50);
  for(const term of ["Machine Learning","Dataset","Target","Accuracy","Precision","Recall","F1-score","Matriz de confusão","Data leakage","Isolation Forest","NLP","TF-IDF","KMeans","Landmark","LLM","Prompt","Dados sintéticos"]){
    const entry=glossaryByTerm.get(term.toLocaleLowerCase("pt-BR"));
    assert.ok(entry,term);
    assert.ok(entry.simple.length > 30,term);
  }
  for(const term of ["Accuracy","Precision","Recall","F1-score"]){
    assert.ok(glossaryByTerm.get(term.toLocaleLowerCase("pt-BR")).technical);
  }
});
