# Datasets sintéticos

`GET /api/datasets` apresenta sete conjuntos: Fisioterapia; monitoramento de Enfermagem; adesão e demanda de Farmácia; animais e acompanhamentos de Veterinária; relatos de Psicologia. A rota `GET /api/datasets/{id}` mostra prévia limitada, valores ausentes, estatísticas apropriadas ao tipo, distribuição e intervalo temporal quando aplicável.

Os downloads CSV/XLSX são oferecidos pelos endpoints especializados. Importação e regeneração continuam nos módulos originais, com validação das colunas e fluxo de confirmação existentes. Registros importados podem aumentar a contagem do banco sem alterar o arquivo padrão baixável.

| Dataset | Tipo de dado | Ações |
| --- | --- | --- |
| Fisioterapia | Tabular | Explorar, importar, baixar, regenerar no módulo |
| Enfermagem | Temporal | Linha do tempo, importar, baixar |
| Farmácia adesão | Tabular | Explorar, importar, baixar |
| Farmácia demanda | Temporal | Explorar, importar, baixar |
| Veterinária animais | Tabular | Explorar, importar, baixar |
| Veterinária acompanhamentos | Temporal | Explorar, importar, baixar |
| Psicologia | Texto | Temas e termos, importar, baixar |

Não inclua dados pessoais em arquivos importados. Os datasets padrão usam seed 42; importações podem ter seed não informada.
