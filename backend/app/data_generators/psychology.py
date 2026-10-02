"""Short, entirely fictional Portuguese narratives for NLP demonstrations."""
from pathlib import Path

import numpy as np
import pandas as pd

AGE_RANGES = ["18-25", "26-35", "36-45", "46-60", "60+"]
CONTEXTS = ["Acadêmico", "Profissional", "Familiar", "Rotina", "Relacionamentos", "Organização pessoal", "Sono", "Mudanças de rotina", "Atividades sociais"]
THEMES = ["Sono", "Preocupação", "Estudos", "Trabalho", "Organização", "Relacionamentos", "Família", "Cansaço", "Mudança", "Atividades sociais", "Rotina", "Motivação"]
COLUMNS = ["record_id", "idade_faixa", "contexto", "texto", "tema_principal", "tema_secundario", "data_sintetica"]

# Os vínculos entre palavras e temas foram construídos artificialmente para fins educacionais.
# As frases não descrevem pessoas reais e os temas não representam categorias clínicas.
FRAGMENTS = {
    "Sono": ["tenho ajustado meus horários de dormir", "acordei mais cedo em alguns dias", "a noite passou rápido e li antes de deitar", "estou observando a regularidade do meu sono", "dormi menos após mudar meus horários", "quero reservar um período mais tranquilo antes de dormir", "ao acordar, anotei como foi a noite", "as tarefas da noite deslocaram a hora de deitar"],
    "Preocupação": ["fiquei pensando em vários compromissos ao mesmo tempo", "algumas dúvidas sobre a semana voltaram à minha atenção", "pensei bastante no que ainda precisava resolver", "a espera por uma resposta ocupou parte do meu tempo", "minhas expectativas mudaram ao longo dos dias", "gostaria de separar os fatos das possibilidades", "reli meus planos mais vezes do que pretendia", "certas pendências apareceram nos meus pensamentos"],
    "Estudos": ["organizei os materiais para uma prova", "revisei anotações da faculdade", "estudei um capítulo novo esta semana", "as atividades do curso exigiram mais tempo", "dividi a leitura em partes menores", "entreguei um trabalho acadêmico", "comparei diferentes formas de aprender o conteúdo", "preparei perguntas para a próxima aula"],
    "Trabalho": ["reorganizei as tarefas do trabalho", "uma reunião alterou a sequência das entregas", "tive vários prazos no escritório", "conversei com a equipe sobre um projeto", "separei o expediente em blocos de atividades", "uma demanda profissional surgiu no fim do dia", "revisei o planejamento de uma entrega", "ajustei minha agenda para uma reunião"],
    "Organização": ["reordenei a lista de tarefas", "tentei organizar melhor meus horários", "anotei prioridades em um caderno", "usei um calendário para distribuir compromissos", "deixei um período livre entre atividades", "revisei o planejamento da semana", "separei tarefas longas em etapas menores", "arrumei minha rotina de anotações"],
    "Relacionamentos": ["conversei com alguém próximo sobre nossos planos", "uma conversa mudou a forma como combinamos os encontros", "tenho reservado tempo para ouvir outra pessoa", "revi expectativas em uma relação", "combinamos um momento para conversar com calma", "percebi diferenças na forma de nos comunicarmos", "troquei mensagens para acertar um encontro", "busquei explicar melhor o que eu queria dizer"],
    "Família": ["participei de uma atividade com a família", "organizamos uma visita entre familiares", "conversei com um parente sobre a semana", "as tarefas de casa foram divididas em família", "um encontro familiar mudou os planos do sábado", "combinei horários com pessoas da minha família", "lembramos juntos de uma viagem antiga", "ajudei a preparar uma reunião de família"],
    "Cansaço": ["terminei o dia com pouca disposição para outras tarefas", "precisei fazer pausas durante as atividades", "a sequência de compromissos deixou meu ritmo mais lento", "reservei um intervalo depois de uma semana cheia", "percebi que meu tempo de descanso ficou curto", "o acúmulo de tarefas exigiu mais pausas", "alguns dias pareceram mais longos que outros", "preferi uma atividade leve no fim da tarde"],
    "Mudança": ["uma mudança de horários alterou meus planos", "comecei uma etapa diferente na rotina", "adaptei meus caminhos após uma novidade", "uma nova organização do dia levou algum tempo", "precisei me acostumar com um ambiente diferente", "mudei a ordem das atividades habituais", "uma transição recente trouxe novas combinações", "a novidade desta semana mudou minha agenda"],
    "Atividades sociais": ["participei de uma atividade em grupo", "combinei um encontro com colegas", "fui a um evento com outras pessoas", "uma conversa coletiva trouxe ideias novas", "reservei tempo para uma reunião social", "encontrei amigos para uma atividade breve", "planejei uma saída no fim de semana", "um convite mudou meus planos para a tarde"],
    "Rotina": ["observei como meus dias têm sido organizados", "o trajeto diário ocupou mais tempo", "ajustei pequenos hábitos durante a semana", "mantive uma sequência parecida de atividades", "meus horários variaram entre os dias", "anotei o que costuma acontecer pela manhã", "reorganizei o começo do dia", "a rotina do fim de semana foi diferente"],
    "Motivação": ["defini uma meta pequena para começar", "retomei um projeto que tinha deixado de lado", "percebi mais interesse em uma atividade nova", "marquei os avanços de uma tarefa longa", "procurei um motivo para concluir uma etapa", "comecei pelo passo mais simples do plano", "uma ideia nova me fez retomar o planejamento", "celebrei ter terminado uma atividade"],
}

OPENINGS = ["Nesta semana,", "Nos últimos dias,", "Hoje,", "Depois de rever minha agenda,", "Ao longo da semana,", "Recentemente,", "Na parte da manhã,", "No fim do dia,"]
NEUTRAL = ["Registrei isso para comparar com outros dias.", "Depois, voltei a olhar o calendário.", "Ainda estou ajustando os próximos passos.", "Isso apareceu nas minhas anotações da semana.", "O contexto mudou um pouco de um dia para outro.", "Quero observar como organizo o tempo."]
CONNECTORS = ["Também", "Além disso,", "Em outro momento,", "Mais tarde,", "Ao mesmo tempo,"]
CONTEXT_BY_THEME = {"Sono": "Sono", "Preocupação": "Rotina", "Estudos": "Acadêmico", "Trabalho": "Profissional", "Organização": "Organização pessoal", "Relacionamentos": "Relacionamentos", "Família": "Familiar", "Cansaço": "Rotina", "Mudança": "Mudanças de rotina", "Atividades sociais": "Atividades sociais", "Rotina": "Rotina", "Motivação": "Organização pessoal"}


def _sentence(text: str) -> str:
    return text[0].upper() + text[1:].rstrip(".") + "."


def generate_reports(size: int = 1000, seed: int = 42) -> pd.DataFrame:
    if size < len(THEMES):
        raise ValueError("O tamanho deve permitir ao menos um registro por tema.")
    rng = np.random.default_rng(seed)
    rows = []
    theme_order = list(np.resize(np.array(THEMES, dtype=object), size))
    rng.shuffle(theme_order)
    for index, primary in enumerate(theme_order, 1):
        secondary = str(rng.choice([theme for theme in THEMES if theme != primary]))
        primary_parts = rng.choice(FRAGMENTS[primary], size=2, replace=False)
        opening = str(rng.choice(OPENINGS))
        sentences = [f"{opening} {primary_parts[0]}."]
        if rng.random() < .76:
            sentences.append(_sentence(f"{rng.choice(CONNECTORS)} {primary_parts[1]}"))
        if rng.random() < .56:
            sentences.append(_sentence(f"{rng.choice(CONNECTORS)} {rng.choice(FRAGMENTS[secondary])}"))
        if rng.random() < .43:
            sentences.append(str(rng.choice(NEUTRAL)))
        text = " ".join(sentences)
        context = CONTEXT_BY_THEME[primary] if rng.random() < .78 else str(rng.choice(CONTEXTS))
        date = (pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 365)))).date().isoformat()
        rows.append([f"PSI-{index:04d}", str(rng.choice(AGE_RANGES)), context, text, primary, secondary, date])
    return pd.DataFrame(rows, columns=COLUMNS)


def export_reports(frame: pd.DataFrame, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_csv(directory / "relatos_psicologia.csv", index=False, encoding="utf-8-sig")
    frame.to_excel(directory / "relatos_psicologia.xlsx", index=False)
