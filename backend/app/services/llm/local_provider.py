from .base import GenerationInput, LLMProvider

TOPIC_DESCRIPTIONS = {
    "Machine Learning": "algoritmos ajustam relações estatísticas a partir de exemplos",
    "Random Forest": "várias árvores de decisão combinam suas previsões",
    "Regressão": "um modelo estima valores numéricos a partir de exemplos",
    "Detecção de anomalias": "um algoritmo busca registros que diferem do padrão aprendido",
    "Isolation Forest": "partições aleatórias ajudam a isolar observações menos comuns",
    "NLP": "textos são transformados em características numéricas para análise",
    "TF-IDF": "termos recebem pesos conforme sua frequência e distinção no conjunto de textos",
    "Clustering": "registros semelhantes são agrupados sem rótulos prévios",
    "Visão Computacional": "informações visuais são convertidas em coordenadas e medidas",
    "Landmarks": "pontos estimados em uma imagem permitem cálculos geométricos",
    "IA Generativa": "um modelo produz texto novo a partir das instruções e do contexto recebido",
}


class LocalTemplateProvider(LLMProvider):
    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "Local Template"

    def generate(self, request: GenerationInput) -> str:
        if request.task == "explain":
            level_prefix = {
                "Simples": "Em linguagem simples: ",
                "Acadêmica": "Na leitura acadêmica do experimento: ",
                "Técnica": "Na leitura técnica do resultado estruturado: ",
            }.get(request.level, "")
            return f"{request.facts}\n\n{level_prefix}{request.details}"
        if request.task == "content":
            statement = TOPIC_DESCRIPTIONS.get(request.topic, "o tema pode ser estudado com dados sintéticos")
            extension = {
                "Básico": "Observe a entrada e a saída antes de interpretar o resultado.",
                "Intermediário": "Compare as variáveis de entrada, o método e a métrica usada na avaliação.",
                "Avançado": "Examine hipóteses, limitações do conjunto de treino e fontes de incerteza.",
            }.get(request.level, "")
            text = f"{request.topic}: {statement}. {extension}"
            if request.length != "Curto":
                text += " Neste laboratório, todos os exemplos são sintéticos e servem para demonstrar o método, não para orientar decisões clínicas."
            if request.length == "Longo":
                text += " Discuta como mudanças no conjunto de dados poderiam alterar a saída e quais informações seriam necessárias para verificar a generalização."
            return text
        if request.task == "question":
            return f"Ao estudar {request.topic}, quais dados e limitações você examinaria antes de interpretar o resultado sintético apresentado?"
        raise ValueError("Tarefa indisponível no modo local.")
