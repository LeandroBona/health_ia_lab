# Modelos de IA

O catálogo `GET /api/models` padroniza ID, módulo, tipo, algoritmo, status, versão, data de treino, dataset e métrica principal. Ele apenas lê metadados dos artefatos já carregados.

| Área | Método | Saída | Avaliação |
| --- | --- | --- | --- |
| Fisioterapia | Random Forest ou Logistic Regression | Categoria e probabilidades | F1 Macro |
| Enfermagem | Isolation Forest | Padrão / anomalia | Métricas de avaliação sintética |
| Farmácia adesão | Classificação supervisionada | Categoria e probabilidades | F1 Macro |
| Farmácia demanda | Regressão temporal | Demanda estimada | MAE |
| Veterinária | Classificação + Isolation Forest | Categoria / registro diferente | F1 Macro / fração marcada |
| Psicologia | TF-IDF + Logistic Regression, KMeans, cosseno | Tema, grupo, similaridade | F1 Macro / contagens |
| Visão Computacional | MediaPipe Pose Landmarker | Landmarks | Sem métrica clínica |
| IA Generativa | OpenAI opcional ou templates locais | Texto explicativo | Não produz previsão |

A inferência é feita em endpoints de cada módulo. O LLM não recalcula valores, scores ou probabilidades; fatos numéricos das explicações são renderizados por código determinístico. Consulte as páginas de cada modelo para métricas detalhadas e limitações do dataset.
