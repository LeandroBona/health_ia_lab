# HealthAI Lab — IA PARA SAÚDE

O **HealthAI Lab** é uma aplicação educacional para demonstrar, em etapas, conceitos de Inteligência Artificial aplicados à Fisioterapia, Enfermagem, Farmácia, Medicina Veterinária e Psicologia.

Esta versão integra Fisioterapia, Enfermagem, Farmácia, Medicina Veterinária, Psicologia, Visão Computacional e IA Generativa em um dashboard, laboratório geral, catálogo de modelos e datasets e histórico educacional.

> O HealthAI Lab foi desenvolvido para demonstração acadêmica de conceitos de Inteligência Artificial e não possui finalidade clínica. Todos os dados usados no projeto devem ser sintéticos.

## Visão geral

A jornada comum é **dado → preparação → modelo especializado → resultado → explicação opcional → decisão humana**. A IA generativa não produz previsões dos modelos especializados; atua como camada opcional de explicação e geração de conteúdo. A webcam é processada localmente no navegador.

Rotas principais: `/` (Dashboard), `/aula` (Modo Aula), `/laboratorio` (experimentos), `/como-funciona` (comparação), `/modelos`, `/datasets`, `/historico`, `/sistema` e `/sobre`. As rotas especializadas de cada área continuam disponíveis, inclusive a rota legada `/fisioterapia/paciente/:id` e o alias `/fisioterapia/pacientes/:id`.

## Modo Aula

O botão **Iniciar Modo Aula** abre uma preparação rápida e depois um percurso de 36 etapas para iniciantes, em layout próprio para projetor. A aula começa com dados e exemplos cotidianos antes dos algoritmos. Há **Modo Professor** compacto e **Explorar sozinho** com instruções ampliadas, glossário em painel ou em `/aula/glossario`, explicações `?`, perguntas com resposta revelável, navegação por botões/setas/espaço, notas ocultas, cronômetro opcional e tela cheia. A etapa e os resultados sintéticos ficam somente no `sessionStorage`; mudanças de tela não entram no histórico. **Reiniciar aula** apaga esse estado temporário.

As demonstrações de Fisioterapia, Enfermagem, Farmácia, Veterinária e Psicologia chamam as APIs existentes. O laboratório NLP aceita texto fictício, mostra tokens, pesos TF-IDF, quatro temas iniciais, similaridade e grupos KMeans. Os IDs são escolhidos entre registros disponíveis por `/api/classroom/scenarios`. A câmera só inicia mediante clique, processa pose no navegador, encerra a tentativa após um tempo limite e oferece um esquema estático claramente identificado quando indisponível. A explicação generativa usa a previsão anterior e funciona com o provider local. Consulte [guia do Modo Aula](documentation/classroom.md).

## Arquitetura

Frontend React → FastAPI → serviços → modelos e SQLite/datasets. Visão Computacional: frontend → Pose Estimation local. IA Generativa: FastAPI → LLMService → OpenAI opcional ou templates locais. Consulte [arquitetura](documentation/architecture.md), [modelos](documentation/models.md), [datasets](documentation/datasets.md) e [guia educacional](documentation/educational-guide.md).

## Tipos de IA

Classificação, regressão, detecção de anomalias, clustering, NLP, visão computacional e geração textual. O catálogo `/api/models` expõe metadados sem executar treinamento.

## Histórico e migrações

`AnalysisHistory` armazena apenas módulo, tipo, modelo, versão, referência sintética, resumo técnico e horário. Explicações generativas têm eventos próprios vinculados ao resultado original quando a referência permite. Prompts, textos completos, frames, imagens e vídeos não são guardados. As migrations do Alembic em `backend/alembic/` preservam bancos legados: a revisão inicial representa as tabelas anteriores e a segunda adiciona o histórico.

No diretório `backend`, para conferir a revisão aplicada: `venv/bin/alembic current`. O backend executa `upgrade head` na inicialização. Faça backup do SQLite antes de alterações manuais no esquema.

## IA Generativa

Sem `OPENAI_API_KEY`, o `LocalTemplateProvider` gera explicações determinísticas e conteúdo didático offline. Para usar a API opcional, configure `OPENAI_API_KEY` e `OPENAI_MODEL` apenas em `backend/.env` (exemplo em `backend/.env.example`). Nunca use prefixo `VITE_` para a chave. O provider externo usa a Responses API com timeout; falhas 401, 429, 500 ou de rede retornam fallback local para explicações. O backend minimiza os dados enviados e renderiza fatos numéricos por código para preservar probabilidades e scores. O construtor de prompts pode ser usado offline; sua execução externa só aparece com provider configurado.

## Endpoints integrados

- `GET /api/models`, `GET /api/datasets`, `GET /api/datasets/{id}`, `GET /api/system/status`.
- `GET /api/history`, `GET /api/history/{id}`, `POST /api/history/vision-session`.
- `GET /api/generative/status`, `POST /api/generative/explain`, `POST /api/generative/content`, `POST /api/generative/question`, `POST /api/generative/prompt/execute`.
- `GET /api/classroom/readiness`, `GET /api/classroom/scenarios`.

## Testes

Backend: `cd backend && venv/bin/python -m pytest -q`. Frontend: `cd frontend && npm test && npm run build`. Docker: `docker compose --env-file .env.production up --build -d`. O volume nomeado conserva SQLite, datasets e artefatos dos modelos.

## Limitações e uso educacional

Todos os resultados vêm de dados sintéticos e não servem para diagnóstico, avaliação clínica, prescrição ou recomendação. Modelos podem errar, dados podem conter vieses, probabilidades não são certezas e a IA generativa pode produzir texto incorreto. A decisão final permanece humana.

## Tecnologias

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, Recharts e Lucide Icons.

**Backend:** Python 3.12+, FastAPI, SQLAlchemy, SQLite, Pandas, Pydantic, OpenPyXL, python-multipart, scikit-learn, joblib e SHAP. Testes com Pytest e HTTPX. Frontend com Node.js 22.12+.

## Estrutura

```text
health-ai-lab/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── data_generators/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── data/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── Dockerfile
├── datasets/
├── documentation/
└── docker-compose.yml
```

## Instalação e execução local

### Backend

No diretório `backend`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No Windows, ative o ambiente virtual com `.venv\Scripts\activate`.

O arquivo SQLite `backend/health_ai_lab.db` é criado automaticamente na primeira inicialização.
O backend também cria os 1000 pacientes padrão (seed 42), exporta CSV/XLSX e os importa para o banco. Reiniciar não regenera nem duplica registros. Um arquivo padrão preexistente é validado antes de ser utilizado. Se apenas um formato estiver ausente, ele é restaurado a partir do outro.
Da mesma forma, cria 500 pacientes fictícios de Enfermagem, com 10–30 medições temporais por paciente, e exporta os dois formatos em `datasets/enfermagem/`. O modelo Isolation Forest é treinado apenas se ainda não existir; análises persistidas são atualizadas quando necessário.
Na primeira inicialização sem modelo salvo, treina os dois algoritmos com os pacientes de origem padrão. Nas demais, carrega o artefato existente sem repetir o treino.

### Frontend

No diretório `frontend`:

```bash
cp .env.example .env
npm install
npm run dev
```

A variável `VITE_API_URL` usa `/api` por padrão. No desenvolvimento, o Vite encaminha essas chamadas ao backend local na porta 8000.

## Endereços padrão

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend: [http://localhost:8000](http://localhost:8000)
- Documentação FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- Dashboard: [http://localhost:8000/api/dashboard](http://localhost:8000/api/dashboard)

## Docker

Na raiz do projeto:

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production up --build -d
```

O frontend ficará disponível somente em `127.0.0.1:8080`; o backend não é publicado no host. O volume `health_ai_data` conserva o banco, os datasets e os modelos. Para domínio público e HTTPS, siga o [guia de deploy em VPS](documentation/vps-deploy.md).

## Módulo de Fisioterapia

Acesse [Fisioterapia](http://localhost:5173/fisioterapia). Os seis indicadores e quatro gráficos usam todos os registros salvos no banco; os filtros afetam somente a tabela paginada. Busque um ID, filtre lesão, sexo e resultado, ou selecione **Ver paciente** para comparar os valores iniciais e atuais. Os resultados são rótulos artificiais do dataset, não previsões ou diagnósticos.

**Explorar Dataset** permite selecionar qualquer coluna. Campos numéricos mostram média, mínimo, máximo, mediana, desvio padrão populacional e distribuição. Campos categóricos mostram contagem por categoria. IDs mostram as primeiras 30 categorias em ordem alfabética para evitar milhares de barras. Os dados validados não admitem ausências; a exploração informa a contagem existente no banco.

## Geração e exportação

Os arquivos padrão são salvos em:

```text
datasets/fisioterapia/pacientes_fisioterapia.csv
datasets/fisioterapia/pacientes_fisioterapia.xlsx
```

O diretório é criado automaticamente. Para gerar explicitamente a partir de `backend`, com o ambiente virtual ativo:

```bash
python -m app.data_generators.physiotherapy --size 1000 --seed 42
```

Se o padrão já existir, a substituição exige `--confirm`:

```bash
python -m app.data_generators.physiotherapy --size 1000 --seed 43 --confirm
```

A mesma seed e o mesmo tamanho reproduzem os mesmos valores e IDs. Os arquivos XLSX podem ter metadados diferentes, mas as células são iguais. Não execute a CLI de regeneração enquanto o servidor estiver ativo; use **Opções do dataset** na interface, com confirmação explícita. Os limites são 1–10.000 pacientes e seed entre 0 e 2147483647.

A regeneração substitui apenas os pacientes associados ao padrão. Pacientes importados são preservados; se houver colisão de IDs com eles, os novos registros padrão conflitantes são ignorados. Por isso o total do arquivo padrão pode diferir do total inserido. Downloads sempre representam o arquivo padrão; estatísticas e tabela representam o banco completo.

Os padrões utilizados neste dataset foram artificialmente construídos para fins educacionais e não representam conhecimento clínico validado.

## Contrato das 18 colunas

A lista centralizada e as regras ficam em `backend/app/schemas/physiotherapy.py`. Os campos numéricos são inteiros; nenhum campo aceita ausência. Não inclua nome, CPF, e-mail, telefone, endereço ou outras colunas pessoais.

| Coluna | Valores aceitos |
| --- | --- |
| patient_id | `PAC-` seguido de 4 a 8 dígitos; exemplo `PAC-0001` |
| idade | 18–85 |
| sexo | Masculino, Feminino, Outro |
| tipo_lesao | Joelho, Ombro, Coluna lombar, Tornozelo, Quadril, Cotovelo, Punho, Lesão muscular, Pós-operatório, Outros |
| tempo_lesao_dias | 1–730 |
| dor_inicial, dor_atual | 0–10 |
| mobilidade_inicial, mobilidade_atual | 0–100 |
| forca_muscular | 1–5 |
| sessoes_previstas | 5–30 |
| sessoes_realizadas, faltas | ≥ 0; a soma não pode exceder sessoes_previstas |
| adesao_exercicios | 0–100 |
| comorbidades | 0–5 |
| indice_funcional_inicial, indice_funcional_atual | 0–100 |
| resultado | recuperacao_adequada, recuperacao_lenta, abandono |

## Importar CSV e XLSX

1. Use **Importar planilha** e baixe um modelo CSV ou XLSX. Os modelos incluem os pacientes padrão: seus IDs serão ignorados se já existirem. Para acrescentar registros, utilize novos IDs sintéticos, por exemplo `PAC-1001`.
2. CSV deve usar UTF-8 (BOM opcional), vírgula ou ponto e vírgula. XLSX utiliza a primeira aba, com cabeçalho na primeira linha. Limites: 5 MB, 10.000 linhas e 50 MB de conteúdo descompactado em XLSX.
3. Selecione ou arraste o arquivo e confirme a origem sintética. Clique em **Validar dados**.
4. Corrija os erros indicados por coluna e linha. A numeração considera o cabeçalho na linha 1. Até 100 linhas com erros são mostradas, junto do total inválido. Não há importação parcial de arquivos inválidos.
5. Revise nome, registros, colunas, tipos, ausências, duplicados e os primeiros 20 registros. Clique em **Importar dados** para gravar.

A prévia não insere pacientes. Dados validados ficam temporariamente no SQLite, associados a um token aleatório que expira em 30 minutos. O frontend não envia caminhos de arquivos. O token é consumido uma única vez; prévias expiradas são removidas na inicialização e ao criar uma nova prévia. Há no máximo 20 prévias pendentes.

Duplicados dentro do arquivo ou já existentes no banco são ignorados; o primeiro registro elegível prevalece. O retorno informa importados, ignorados e total. A contagem é recalculada na confirmação. Uma importação só cria uma entrada no catálogo de datasets quando insere ao menos um paciente.

## API do módulo

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| GET | `/api/fisioterapia/patients` | page, page_size (1–100), search (ID), resultado, tipo_lesao, sexo |
| GET | `/api/fisioterapia/patients/{patient_id}` | Ficha completa ou erro 404 |
| GET | `/api/fisioterapia/stats` | Estatísticas e distribuições do banco |
| GET | `/api/fisioterapia/schema` | Contrato de colunas, faixas e categorias |
| POST | `/api/fisioterapia/upload/preview` | Upload multipart no campo `file`; validação e token |
| POST | `/api/fisioterapia/upload` | Alias de preview; não salva pacientes |
| POST | `/api/fisioterapia/upload/confirm` | JSON `{"token":"..."}`; importação definitiva |
| GET | `/api/fisioterapia/dataset` | Metadados do padrão |
| GET | `/api/fisioterapia/dataset/download/csv` | Baixar o padrão CSV |
| GET | `/api/fisioterapia/dataset/download/xlsx` | Baixar o padrão XLSX |
| POST | `/api/fisioterapia/dataset/regenerate` | JSON `{"size":1000,"seed":42,"confirm":true}` |
| GET | `/api/fisioterapia/explore?column=idade` | Exploração da coluna no banco completo |

Variáveis opcionais no backend: `DATABASE_URL`, `DATASETS_DIR` (diretório pai de `fisioterapia`) e `CORS_ORIGINS`. O `.env` é lido de `backend/.env`. Sem `CORS_ORIGINS`, o desenvolvimento aceita frontends locais nas portas `51xx`, inclusive quando o Vite escolhe 5174 ou 5175. Definir `CORS_ORIGINS` restringe as origens explicitamente. Por padrão os caminhos são absolutos e relativos à raiz do projeto, independentemente do diretório de execução.

Esta etapa destina-se ao ambiente acadêmico local, com um único processo Uvicorn. O endpoint administrativo exige confirmação, mas ainda não há usuários ou autenticação: não publique esta configuração na internet.

## Testes

Em `backend`, com o ambiente virtual ativo:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes usam SQLite e diretórios temporários isolados, sem alterar o dataset de trabalho. Cobrem reprodutibilidade, faixas, colunas, arquivos, preview, confirmação, duplicidades, expiração, filtros, paginação, consulta individual, estatísticas e regeneração.

Em `frontend`:

```bash
npm run build
```

## Machine Learning de Fisioterapia — Parte 3

Acesse **Fisioterapia > Modelo de IA**. O treinamento compara Random Forest (200 árvores, `class_weight="balanced"`, seed 42) e Logistic Regression (`class_weight="balanced"`, máximo de 2000 iterações). O selecionado é o de maior **F1 macro** no mesmo conjunto de teste. Em empate exato, Random Forest prevalece por ordem estável. Ambos os resultados permanecem visíveis.

São usadas as 16 variáveis do paciente, excluindo `patient_id` e `resultado`. A divisão é estratificada, com 80% de treino e 20% de teste, `random_state=42`. O pré-processamento inteiro está na pipeline salva: imputação numérica pela mediana, imputação categórica pela moda e OneHotEncoder. Apenas Logistic Regression recebe StandardScaler. O pré-processador aprende exclusivamente com o conjunto de treino. A pipeline selecionada não é reajustada com os dados de teste.

Na primeira inicialização, o treino utiliza o padrão. **Treinar com dados atuais** usa todos os registros atuais no banco, inclusive as importações. São necessários ao menos 30 registros e 5 exemplos de cada classe; erros não substituem o modelo anterior. Apenas um treino é permitido por vez. Importação e regeneração não disparam novo treinamento; a tela informa quando a fonte usada no último treino mudou.

A avaliação inclui accuracy, precision macro, recall macro, F1 macro, matriz de confusão, classification report e métricas por classe. As linhas da matriz são resultados registrados; as colunas são previsões. A mesma divisão de teste é usada para comparar e selecionar os algoritmos, portanto os números servem a esta demonstração e não constituem uma avaliação externa independente.

Na ficha de um paciente, **Executar análise** mostra classe, probabilidades, maior probabilidade (confiança), resultado original, acerto/erro e se o registro participou do treino, do teste ou mudou desde então. O formulário **Previsão manual** aceita somente as 16 features e não cria um paciente. As categorias, faixas e regras de sessões são validadas pela API. `patient_id` e `resultado` são rejeitados no formulário da API manual.

As probabilidades são estimativas não calibradas do classificador. Como o dataset inclui indicadores atuais, a demonstração classifica o estado registrado; não é um estudo temporal prospectivo de evolução. As relações e os rótulos são artificiais, e as métricas não devem ser apresentadas como evidência de utilidade clínica.

> Este modelo foi treinado exclusivamente com dados sintéticos e relações artificialmente construídas para fins educacionais. Seus resultados não possuem validade clínica.

### Artefatos e versionamento

```text
backend/models/physiotherapy/physiotherapy_model.joblib
backend/models/physiotherapy/model_metadata.json
```

O artefato joblib contém a pipeline, os metadados correspondentes e hashes dos registros para identificar sua participação no treino/teste. O JSON inclui algoritmo, versão, timestamp UTC, registros, features, seed, métricas, resultados dos dois algoritmos, duração, versão do scikit-learn e impressão digital da fonte. A versão progride de `1.0` para `2.0` a cada novo treino. A troca do joblib é atômica; previsões em andamento utilizam o modelo anterior até a publicação bem-sucedida do novo.

Somente artefatos locais produzidos pela aplicação são carregados. Nunca substitua o arquivo joblib por arquivos de terceiros, pois esse formato permite execução de código durante o carregamento. Um artefato incompatível não é carregado; a tela solicita novo treinamento. `MODELS_DIR` pode configurar o diretório pai de `physiotherapy`; no Docker, os modelos persistem em `/data/models`.

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| POST | `/api/fisioterapia/model/train` | Treinar os dois algoritmos com os dados atuais do banco |
| GET | `/api/fisioterapia/model` | Modelo, status, versão, fonte, features, métricas e mudanças no dataset |
| GET | `/api/fisioterapia/model/evaluation` | Matriz, métricas por classe e comparação de algoritmos |
| POST | `/api/fisioterapia/predict/{patient_id}` | Classificar registro existente e comparar com seu resultado |
| POST | `/api/fisioterapia/predict` | Classificar JSON com as 16 features, sem ID nem alvo |

Os testes também verificam ausência de vazamento do alvo, exclusão do ID, soma das probabilidades, seleção por F1, coerência da matriz, persistência, versão e carregamento sem retreino.

## Explicabilidade e simulador — Parte 4

**Explicabilidade** ajuda a examinar quais entradas contribuíram para uma saída do modelo. O SHAP compara a saída de um registro com uma referência matemática e distribui a diferença entre as variáveis. O backend calcula SHAP apenas quando solicitado: `TreeExplainer` para Random Forest ou `LinearExplainer` para Logistic Regression. O cálculo recebe as colunas já transformadas pela pipeline salva; as categorias criadas pelo OneHotEncoder são agrupadas novamente sob `Sexo` e `Tipo de lesão`. Nomes e rótulos ficam centralizados em `feature_config.py` e na apresentação.

A **importância global** mostra a magnitude média absoluta das contribuições SHAP em uma amostra determinística de até 60 registros da divisão de teste. Os valores são normalizados para somarem 1 e ordenados. A **explicação individual** mostra, para a classe selecionada, as contribuições positivas e negativas de um registro, seu valor original e uma intensidade relativa aos próprios fatores daquele registro. Para Random Forest os impactos são apresentados em pontos percentuais da probabilidade da classe, relativos à referência do modelo. Para Logistic Regression são unidades do escore interno (logit), não pontos percentuais. A explicação individual mostra os 10 maiores impactos e as três probabilidades continuam visíveis.

Abra **Fisioterapia > Modelo de IA** para o gráfico global; na ficha do paciente execute a análise e clique **Explicar esta previsão**. O mesmo botão está disponível em **Fisioterapia > Laboratório** após classificar um registro preenchido manualmente. O formulário manual não salva pacientes. A explicação é calculada sob demanda; um cache simples em memória guarda o explicador e a importância global da versão ativa, sendo invalidado automaticamente quando um novo modelo substitui o anterior.

Em **Fisioterapia > Simulador**, busque um `patient_id`, escolha um paciente aleatório ou entre pela ficha individual. Os sliders alteram apenas sete campos permitidos. Clique **Recalcular previsão** para comparar as três probabilidades antes e depois, inclusive a variação em pontos percentuais. **Restaurar valores originais** recupera os dados e a classificação inicial. Cenários A, B e C usam nomes neutros e podem ser comparados em tabela e gráfico; o histórico guarda as últimas oito simulações apenas enquanto a página estiver aberta. A análise de sensibilidade varia um campo numérico permitido por vez, mantendo os demais constantes. Sessões e faltas respeitam conjuntamente o total previsto.

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| GET | `/api/fisioterapia/model/feature-importance` | Importância global SHAP da amostra de teste |
| GET | `/api/fisioterapia/patients/{patient_id}/explanation` | Explicação individual de paciente existente |
| POST | `/api/fisioterapia/predict/explain` | Classificação e explicação de 16 features manuais |
| POST | `/api/fisioterapia/simulate` | `{"patient_id":"PAC-0042","changes":{"adesao_exercicios":80}}` |
| POST | `/api/fisioterapia/simulate/feature` | `{"patient_id":"PAC-0042","feature":"adesao_exercicios","values":[0,10,20,30,40,50,60,70,80,90,100]}` |

Todas as simulações operam em memória, validam as faixas e a relação entre sessões e faltas, e não alteram o SQLite. Os valores SHAP e as variações de probabilidade descrevem exclusivamente associações e respostas matemáticas do modelo treinado com dados sintéticos. Uma alteração em uma variável pode estar fora das relações artificiais típicas do dataset; o efeito calculado **não implica causalidade nem efeito em pacientes reais**. As probabilidades não foram calibradas para interpretação clínica, e a seleção do algoritmo usou a mesma divisão de teste apresentada nas métricas.

## Enfermagem — Parte 5

Acesse [Enfermagem](http://localhost:5173/enfermagem) para visualizar medições sintéticas, filtrar registros por paciente, período e classificação, abrir o histórico temporal e comparar uma medição às médias do próprio paciente fictício e do dataset. A página [Laboratório](http://localhost:5173/enfermagem/laboratorio) analisa valores alterados manualmente sem gravar no banco. O botão de exemplo anômalo prepara valores mais afastados do padrão, mas a classificação final sempre vem do Isolation Forest; não há limites clínicos manuais.

O gerador `backend/app/data_generators/nursing.py` usa seed 42 por padrão e produz 500 identificadores `ENF-0001` etc., com 10–30 medições `MED-000001` etc. por paciente. Cada paciente tem uma linha de base artificial e variações pequenas, com aproximadamente 5–10% de medições alteradas por uma de várias perturbações artificiais. A mesma seed e o mesmo tamanho geram os mesmos registros. O backend gera o dataset automaticamente na primeira inicialização, e guarda:

```text
datasets/enfermagem/monitoramento_enfermagem.csv
datasets/enfermagem/monitoramento_enfermagem.xlsx
backend/models/nursing/nursing_isolation_forest.joblib
backend/models/nursing/model_metadata.json
```

As 12 colunas obrigatórias são `measurement_id`, `patient_id`, `timestamp`, `idade`, `frequencia_cardiaca`, `frequencia_respiratoria`, `temperatura`, `pressao_sistolica`, `pressao_diastolica`, `saturacao`, `nivel_dor` e `estado`. `timestamp` deve conter fuso horário. `estado` vale `padrao` ou `alterado` e é conhecido somente porque as alterações são produzidas artificialmente. Não use nome, CPF, contato ou outras colunas pessoais.

O pipeline contém `SimpleImputer`, `StandardScaler` e `IsolationForest` com seed 42 e `contamination=0.07`. Usa apenas os sete sinais numéricos: nunca recebe IDs, timestamp, idade ou `estado` como features. A coluna `estado` é usada **somente após a predição** para calcular precision, recall, F1 e matriz de confusão didáticos. O índice exibido é o oposto do `decision_function`: quanto maior, mais distante matematicamente do padrão aprendido. Ele não representa risco, gravidade ou diagnóstico. O modelo é carregado na reinicialização e retreinado apenas pelo botão/endpoint de treino; novos registros importados são analisados com o modelo atual, sem retreinamento automático.

Em [Dataset de Enfermagem](http://localhost:5173/enfermagem/dataset), selecione uma coluna para explorar distribuição, ausências e estatísticas; a aba **Série temporal** mostra contagens diárias. Para importar, vá a [Importar planilha](http://localhost:5173/enfermagem/importar), selecione CSV UTF-8 ou XLSX (primeira aba), valide e confira até 20 linhas de prévia. Só então confirme. O limite é 5 MB e 20.000 linhas por arquivo; o XLSX descompactado não pode exceder 50 MB. Colunas extras são rejeitadas; IDs de medição já existentes são ignorados e informados. Prévia e confirmação usam token temporário, não caminhos informados pelo frontend. O dataset padrão pode ser baixado na visão geral ou na página de exploração.

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| GET | `/api/enfermagem/stats` | Pacientes, medições, anomalias e última análise |
| GET | `/api/enfermagem/patients` | Paginação e busca por ID |
| GET | `/api/enfermagem/patients/{patient_id}` | Resumo e médias do paciente |
| GET | `/api/enfermagem/patients/{patient_id}/measurements` | Histórico paginado |
| GET | `/api/enfermagem/measurements` | Filtros por paciente, classificação e período |
| GET | `/api/enfermagem/measurements/{measurement_id}` | Medição e comparações estatísticas |
| GET | `/api/enfermagem/model` | Metadados e versão |
| GET | `/api/enfermagem/model/evaluation` | Avaliação didática contra `estado` |
| POST | `/api/enfermagem/model/train` | Retreinar e analisar medições |
| POST | `/api/enfermagem/anomalies/analyze` | Reanalisar todas as medições |
| POST | `/api/enfermagem/anomalies/predict` | Analisar sete sinais manuais, sem salvar |
| GET | `/api/enfermagem/dataset/explore?column=temperatura` | Distribuição e estatísticas |
| GET | `/api/enfermagem/dataset/timeline` | Contagem diária de medições e anomalias |
| GET | `/api/enfermagem/dataset/download/{csv|xlsx}` | Baixar padrão |
| POST | `/api/enfermagem/upload/preview` | Validar arquivo e criar prévia |
| POST | `/api/enfermagem/upload/confirm` | Inserir registros validados, ignorando duplicados |

As faixas do schema são barreiras para dados sintéticos impossíveis e **não são critérios diagnósticos**. Uma medição pode ser classificada como anomalia mesmo dentro das faixas, ou como padrão próximo das extremidades, porque a decisão é feita pelo modelo. O conjunto de treinamento e a avaliação didática usam o mesmo dataset sintético; essas métricas não medem desempenho clínico nem capacidade de generalização externa. O treinamento e a análise global podem demorar alguns segundos em máquinas modestas.

## Farmácia — Parte 6

Acesse [Farmácia](http://localhost:5173/farmacia) para comparar dois problemas: **classificação**, cuja saída é uma categoria com probabilidades, e **regressão**, cuja saída é um número estimado. Todos os produtos e acompanhamentos são inteiramente fictícios; os resultados não orientam uso de medicamentos, tratamento ou estoque real.

Na primeira inicialização, o backend cria 1.000 registros de adesão (`FAR-0001` etc.) e 36 meses de histórico para 20 produtos (`MED-001` etc.), seed 42. Os arquivos aparecem em:

```text
datasets/farmacia/adesao_farmacia.csv
datasets/farmacia/adesao_farmacia.xlsx
datasets/farmacia/demanda_farmacia.csv
datasets/farmacia/demanda_farmacia.xlsx
```

Os geradores `app.data_generators.pharmacy_adherence.generate_adherence(size=1000, seed=42)` e `app.data_generators.pharmacy_demand.generate_demand(medications=20, months=36, seed=42)` podem ser chamados em Python para exercícios reprodutíveis. Para criar os arquivos usados pela aplicação, basta iniciar o backend; ele importa os padrões para SQLite somente quando ausentes e restaura formatos faltantes a partir do banco. Novos arquivos importados não substituem o padrão nem alteram automaticamente o modelo treinado.

### Laboratório de adesão

As 13 colunas são `patient_id`, `idade`, `quantidade_medicamentos`, `doses_diarias`, `tempo_tratamento_dias`, `esquecimentos_30_dias`, `retiradas_atrasadas`, `consultas_acompanhamento`, `usa_organizador`, `recebe_lembretes`, `complexidade_rotina`, `adesao_percentual` e `categoria_adesao`. A categoria é `alta`, `moderada` ou `baixa`. As relações entre variáveis foram definidas artificialmente; não representam evidência clínica ou farmacológica.

O modelo usa apenas os dez campos entre `idade` e `complexidade_rotina`. **Não usa** ID, `adesao_percentual` ou `categoria_adesao`: o percentual ajuda a gerar a classe e incluí-lo como feature criaria vazamento da resposta. `LogisticRegression` e `RandomForestClassifier` usam pipelines com imputação, codificação categórica e, para a regressão logística, escala numérica. A divisão é estratificada 80/20, seed 42; o modelo de maior F1 macro no teste é salvo em `backend/models/pharmacy/adherence/`. São exibidas accuracy, precision macro, recall macro, F1 macro, matriz de confusão, três probabilidades e comparação dos algoritmos. A amostra de teste também seleciona o algoritmo, portanto as métricas não são validação externa independente.

Use [Adesão](http://localhost:5173/farmacia/adesao) para ver gráficos, tabela paginada, registro individual e [formulário manual](http://localhost:5173/farmacia/adesao/laboratorio). O formulário não salva dados.

### Laboratório de demanda

As 12 colunas são `medication_id`, `month`, `year`, `period`, `stock_initial`, `quantity_received`, `quantity_used`, `stock_final`, `seasonality_index`, `trend_index`, `promotion_event` e `demand`. O alvo do modelo é **`demand` do período corrente** durante o treinamento; para a previsão seguinte, as features são construídas a partir dos seis períodos anteriores e do calendário do próximo mês. `quantity_used` e `promotion_event` do futuro não são utilizados, pois não são conhecidos antecipadamente.

Cada série sintética inclui tendência, sazonalidade, ruído e picos ocasionais. `lag_1`, `lag_2`, `lag_3` e médias móveis de 3 e 6 meses são calculados com `shift(1)`, exclusivamente com valores anteriores. A divisão é cronológica: primeiros 80% dos meses válidos para treino e últimos 20% para teste. Em séries temporais, informações futuras não devem ser usadas para prever o passado. `LinearRegression` e `RandomForestRegressor` são comparados por MAE; o menor MAE define o modelo ativo. RMSE penaliza erros maiores e R² resume a variação explicada no teste. Artefatos ficam em `backend/models/pharmacy/demand/`.

Use [Demanda](http://localhost:5173/farmacia/demanda) para ver séries, tabela de produtos e comparação observado versus previsto; o [laboratório](http://localhost:5173/farmacia/demanda/laboratorio) mostra os lags e a previsão seguinte. A estimativa não é uma recomendação de compra.

### Uploads e API

Ambos os laboratórios aceitam CSV UTF-8 e XLSX na tela **Importar**. O fluxo é selecionar → validar → revisar até 20 linhas → confirmar. Arquivos têm limite de 5 MB/10.000 linhas; colunas adicionais são recusadas para evitar dados pessoais. Uma prévia com token aleatório expira em 30 minutos. IDs `patient_id` já existentes ou pares `(medication_id, period)` já existentes são ignorados, e as contagens de importados/ignorados são informadas. Não há leitura de caminhos enviados pelo frontend. A validação central fica em `backend/app/schemas/pharmacy.py` e `backend/app/services/pharmacy_dataset.py`.

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| GET | `/api/farmacia/adesao/patients`, `/patients/{id}`, `/stats` | Lista paginada, registro e indicadores |
| GET/POST | `/api/farmacia/adesao/model`, `/model/evaluation`, `/model/train` | Metadados, avaliação e retreinamento |
| POST | `/api/farmacia/adesao/predict`, `/predict/{id}` | Classificação manual ou existente |
| GET | `/api/farmacia/demanda/medications`, `/medications/{id}`, `/stats` | Produtos, séries e indicadores |
| GET/POST | `/api/farmacia/demanda/model`, `/model/evaluation`, `/model/train` | Metadados, avaliação e retreinamento |
| POST | `/api/farmacia/demanda/predict/{id}` | Próximo mês de produto fictício |
| POST | `/api/farmacia/{adesao|demanda}/upload/preview`, `/upload/confirm` | Prévia e importação confirmada |
| GET | `/api/farmacia/{adesao|demanda}/dataset/download/{csv|xlsx}` | Arquivo padrão |

O `joblib` é carregado somente dos diretórios locais da aplicação; não aceite artefatos de terceiros. O uso é acadêmico/local, sem autenticação. Os testes em `backend/tests/test_pharmacy.py` cobrem geração, reprodutibilidade, colunas, faixas, uploads CSV/XLSX, duplicidade, persistência, previsão, ordem temporal e um teste explícito que altera demanda futura e confirma que features passadas não mudam.

## Medicina Veterinária

Acesse [Veterinária](http://localhost:5173/veterinaria) para explorar aproximadamente 1.000 animais totalmente fictícios, filtrar a tabela, abrir uma ficha, executar a classificação e observar acompanhamentos temporais. O [laboratório](http://localhost:5173/veterinaria/laboratorio) aceita registros manuais e três exemplos. A [página de modelos](http://localhost:5173/veterinaria/modelo) compara as métricas de classificação e descreve o detector de anomalias. A [página de datasets](http://localhost:5173/veterinaria/importar) oferece download e importação.

**Os dados e resultados apresentados neste módulo são sintéticos e possuem finalidade exclusivamente educacional.** As categorias `evolucao_esperada`, `acompanhamento_adicional` e `dados_insuficientes` são rótulos artificiais do dataset. O sistema não realiza diagnóstico nem fornece orientação veterinária. As faixas dos geradores e formulários servem apenas à consistência do exemplo.

### Dados e relações

`app.data_generators.veterinary.generate_animals(size=1000, seed=42)` cria IDs `VET-0001` em diante e os campos `animal_id`, `especie`, `idade_anos`, `peso_kg`, `sexo`, `procedimento`, `dias_pos_procedimento`, `temperatura`, `frequencia_cardiaca`, `atividade_percentual`, `alimentacao_percentual`, `hidratacao_percentual`, `medicacao_administrada_percentual`, `retornos_realizados`, `retornos_previstos`, `alteracoes_reportadas`, `indice_recuperacao` e `evolucao`. Alimentação, atividade, retornos e outros indicadores influenciam artificialmente a frequência das classes, com ruído. A classe `dados_insuficientes` é mais comum em registros com poucos dias e sem retornos; o gerador padrão não simula campos ausentes. Essa construção não representa evidência veterinária validada.

`app.data_generators.veterinary_followup.generate_followups` cria 10 a 20 registros para uma parte dos animais, com `followup_id`, `animal_id`, `timestamp`, temperatura, frequência cardíaca, atividade, alimentação, hidratação e alterações reportadas. O banco relaciona `VeterinaryAnimal` 1:N `VeterinaryFollowUp`. Os arquivos são gerados na inicialização, com seed 42, em `datasets/veterinaria/animais_veterinaria.{csv,xlsx}` e `datasets/veterinaria/acompanhamento_veterinario.{csv,xlsx}`. Geradores aceitam seed para reprodução.

### Classificação e anomalias

A classificação usa as 16 colunas de características entre `especie` e `indice_recuperacao`. **`animal_id` e `evolucao` não são features.** O alvo sintético é calculado a partir do registro consolidado da mesma observação; os acompanhamentos temporais não entram nessa pipeline. O pré-processamento salvo inclui `ColumnTransformer`, `SimpleImputer`, `OneHotEncoder` e `StandardScaler`. `RandomForestClassifier` e `LogisticRegression` são comparados em uma divisão estratificada 80/20 (`random_state=42`) por accuracy, precision macro, recall macro e F1 macro. O maior F1 macro seleciona o modelo. A amostra de teste também seleciona o algoritmo, portanto as métricas não são uma validação externa independente. O artefato e seus metadados ficam em `backend/models/veterinary/veterinary_model.joblib` e `model_metadata.json`.

O segundo modelo usa `IsolationForest` sobre seis indicadores dos acompanhamentos. **`animal_id`, `followup_id` e `timestamp` não são features.** O pipeline salvo imputa e escala os valores. A saída é `padrao` ou `anomalia`, com índice de anomalia; um índice maior indica maior diferença em relação ao padrão do próprio dataset. A fração marcada não mede desempenho clínico, pois não existem rótulos independentes de anomalia. O artefato fica em `backend/models/veterinary/veterinary_anomaly_model.joblib`.

### API e importação

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| GET | `/api/veterinaria/animals`, `/animals/{animal_id}`, `/stats` | Lista filtrável, ficha e indicadores |
| GET/POST | `/api/veterinaria/model`, `/model/evaluation`, `/model/train` | Metadados, métricas e treino |
| POST | `/api/veterinaria/predict`, `/predict/{animal_id}` | Classificação manual ou de um animal cadastrado |
| GET/POST | `/api/veterinaria/anomalies/model`, `/anomalies/model/train` | Metadados e retreinamento do detector |
| GET | `/api/veterinaria/animals/{animal_id}/anomalies` | Acompanhamentos analisados |
| POST | `/api/veterinaria/anomalies/analyze`, `/anomalies/predict` | Análise dos registros ou de um registro manual |
| GET | `/api/veterinaria/{animals\|followups}/dataset/download/{csv\|xlsx}` | Arquivo sintético padrão |
| POST | `/api/veterinaria/{animals\|followups}/upload/preview`, `/upload/confirm` | Validação e importação em duas etapas |

Uploads CSV/XLSX têm limite de 5 MB e 10.000 linhas. A prévia mostra colunas, tipos, ausências e 20 registros; um token expira em 30 minutos e só pode ser confirmado uma vez. Colunas adicionais são recusadas para evitar dados pessoais, IDs repetidos são ignorados, e acompanhamentos precisam referenciar animais existentes. O esquema central está em `backend/app/schemas/veterinary.py`. Importações não retreinam automaticamente os modelos. Testes estão em `backend/tests/test_veterinary.py`.

## Psicologia — Parte 8: NLP educacional

Acesse [Psicologia](http://localhost:5173/psicologia) para explorar relatos fictícios, distribuição dos temas e contextos, termos e bigramas frequentes, cinco grupos descobertos sem rótulos e uma tabela filtrável. A ficha de cada relato mostra o texto original, tema registrado, tema previsto, probabilidades, palavras-chave, cinco textos semelhantes e grupo aproximado. O [laboratório](http://localhost:5173/psicologia/laboratorio) aceita um texto fictício e oferece cinco exemplos, além de mostrar tokens, stopwords removidas, termos mantidos e um vetor TF-IDF simplificado. A [página de modelos](http://localhost:5173/psicologia/modelo) mostra métricas e matriz de confusão; a [página de datasets](http://localhost:5173/psicologia/importar) permite baixar e importar CSV/XLSX.

> Este módulo analisa características linguísticas de textos sintéticos e não realiza diagnóstico psicológico, avaliação clínica ou interpretação da condição emocional de uma pessoa real.

### Dataset e representação

`app.data_generators.psychology.generate_reports(size=1000, seed=42)` cria cerca de mil relatos de uma a cinco frases com IDs `PSI-0001` em diante. Os campos são `record_id`, `idade_faixa`, `contexto`, `texto`, `tema_principal`, `tema_secundario` e `data_sintetica`. Há 12 temas linguísticos, como Estudos, Sono e Organização. Termos e temas possuem relações artificiais com variação e mistura entre assuntos. Os textos não contêm nomes ou dados pessoais. O padrão é salvo em `datasets/psicologia/relatos_psicologia.csv` e `.xlsx`; a seed permite reproduzir a geração.

O pré-processamento converte para minúsculas, remove pontuação e espaços extras, tokeniza e remove uma lista local de stopwords em português. O texto original permanece intacto na interface. O `TfidfVectorizer` usa unigramas e bigramas, `min_df=2` e no máximo 2.000 features. O TF-IDF transforma palavras em números considerando a importância de cada termo dentro dos textos. Os pesos exibidos no laboratório são componentes do vetor matemático, não intensidade de uma condição pessoal.

### Classificação, similaridade e clustering

A classificação usa a pipeline `TF-IDF → LogisticRegression` com divisão estratificada 80%/20% e `random_state=42`. **Somente `texto` é entrada.** `record_id`, `tema_principal`, contexto, idade e data não entram no classificador. O tema registrado é apenas o alvo supervisionado; as frases não inserem o rótulo de forma literal, como “meu tema é Sono”. A avaliação mostra accuracy, precision macro, recall macro, F1 macro e matriz de confusão. As probabilidades representam a saída do classificador nos temas deste dataset.

A busca de relatos semelhantes usa similaridade de cosseno entre vetores TF-IDF; o próprio texto consultado é excluído quando pertence ao dataset. Similaridade é proximidade matemática, não equivalência de experiências pessoais. O `KMeans` separa os vetores em cinco grupos numerados, sem receber `tema_principal` e sem atribuir significado psicológico aos grupos. Cada grupo mostra quantidade, termos representativos e exemplos. Os artefatos locais ficam em `backend/models/psychology/psychology_topic_model.joblib` e `model_metadata.json`. A importação não retreina automaticamente; o botão **Treinar novamente** usa o banco atual. Os modelos são leves e executam em CPU, sem serviços externos.

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| GET | `/api/psicologia/stats`, `/records`, `/records/{record_id}` | Indicadores, filtros e ficha de relato |
| GET | `/api/psicologia/terms?limit=10&tema=Estudos&contexto=Acadêmico` | Termos, bigramas e termos por tema |
| GET | `/api/psicologia/clusters` | Cinco grupos, tamanhos, termos e exemplos |
| GET/POST | `/api/psicologia/model`, `/model/evaluation`, `/model/train` | Metadados, métricas e retreinamento |
| POST | `/api/psicologia/keywords`, `/classify`, `/similarity`, `/analyze` | Análises de `{"text":"..."}`; a última reúne todo o fluxo |
| GET | `/api/psicologia/dataset/download/{csv\|xlsx}` | Dataset padrão |
| POST | `/api/psicologia/upload/preview`, `/upload/confirm` | Importação com prévia e token de uso único |

Uploads exigem `record_id`, `texto`, `tema_principal` e `contexto`; as outras três colunas são opcionais. A validação central rejeita textos vazios, categorias fora da lista, colunas extras e formatos evidentes de email, CPF e telefone. A prévia mostra linhas, colunas, tipos, ausências, comprimento médio, temas e até 20 registros. IDs já existentes são ignorados. O limite compartilhado de arquivo é 5 MB. Testes do módulo estão em `backend/tests/test_psychology.py`.

Os textos e seus rótulos foram criados por regras didáticas; as métricas não medem utilidade clínica nem generalização para relatos reais. O conjunto de teste é da mesma geração sintética do treino. Nenhuma saída constitui diagnóstico ou avaliação psicológica.

## Visão Computacional — Parte 9

Acesse [Visão Computacional](http://localhost:5173/visao-computacional) para ver o fluxo **câmera → imagem → modelo → landmarks → coordenadas → cálculos → métricas de movimento**. O [laboratório](http://localhost:5173/visao-computacional/laboratorio) permite ativar e desativar a webcam, selecionar um dispositivo, acompanhar a sobreposição de pontos e conexões, ler a visibilidade dos 13 pontos principais, comparar cotovelos e joelhos, visualizar uma série temporal e contar ciclos simples do ângulo selecionado.

> Este módulo realiza estimativa computacional de pose para fins educacionais. Os ângulos e métricas apresentados não representam avaliação clínica, diagnóstico ou recomendação fisioterapêutica.

A implementação usa `@mediapipe/tasks-vision` 1.0.1 e o Pose Landmarker Lite. A biblioteca, seus arquivos WebAssembly e o modelo `.task` são servidos pela aplicação; não há chamada a uma API de inferência externa. `frontend/src/vision/poseService.ts` encapsula o provider, permitindo substituição futura. A câmera só é solicitada ao clicar em **Ativar câmera**. A saída da página e o botão **Desativar câmera** param todas as tracks. Frames e imagens não são gravados nem enviados ao backend. Uma sessão só é salva após clicar em **Registrar sessão numérica**, com tempos, quatro ângulos e contagem; o armazenamento é local ao navegador e limitado às 20 sessões mais recentes e a 1.200 amostras por sessão.

`calculateAngle(pointA, vertex, pointC)` utiliza o produto escalar entre dois vetores e retorna 0–180 graus. As coordenadas normalizadas são convertidas para pixels antes do cálculo para respeitar a proporção do vídeo. Se um dos três pontos tiver visibilidade ou presença abaixo de 0,55, o ângulo fica indisponível. A prévia e o canvas são espelhados apenas visualmente; os nomes esquerdo e direito mantêm os índices anatômicos do modelo. A contagem didática usa histerese: ângulo abaixo de 100° seguido de ângulo acima de 150° conta um ciclo. Esses limites não são parâmetros clínicos.

O funcionamento depende de navegador com `getUserMedia`, acesso à câmera e suporte ao WebAssembly do MediaPipe; `localhost` ou HTTPS são necessários para solicitar a câmera. Ângulos em 2D variam com perspectiva, enquadramento e oclusão. O [aviso oficial de privacidade do MediaPipe](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/web/vision/README.md#privacy-notice) informa que a biblioteca processa imagens no dispositivo, mas pode enviar métricas de uso e desempenho ao Google; essa informação aparece antes da ativação da câmera. Não há avaliação fisioterapêutica, interpretação clínica ou recomendação de tratamento. Testes de geometria, confiança, espelhamento, contagem e persistência numérica: `cd frontend && npm test`; o build completo usa `npm run build`.

Os arquivos locais do modelo foram obtidos da [documentação oficial do Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/web_js) e do [repositório oficial de exemplos](https://github.com/google-ai-edge/mediapipe-samples-web/blob/main/src/tasks/pose-landmarker.ts). O pacote foi instalado pelo npm; o modelo Lite foi obtido de `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`.
