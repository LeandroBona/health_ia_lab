# Modo Aula

Abra `/aula` pelo Dashboard. A tela de preparação consulta `GET /api/classroom/readiness` e mostra quais módulos estão disponíveis. Ela lê metadados; não treina nem executa modelos. Um módulo indisponível pode ser pulado.

## Controles

- **Próximo / Anterior:** botões ou setas. Espaço avança quando o foco não está em um controle interativo.
- **Etapas:** salto direto entre as 36 telas, agrupadas em Conceitos básicos, Machine Learning, NLP, Visão Computacional, IA Generativa e Conclusão. **Notas:** orientações do professor em painel oculto por padrão.
- **Modo Aluno / Modo Professor:** o primeiro mostra quatro perguntas de orientação em cada experimento; o segundo compacta as instruções. Ambos permitem pular etapas.
- **Glossário:** painel dentro da aula e rota `/aula/glossario` com busca, definições simples e fórmulas opcionais. Botões `?` explicam termos no contexto.
- **Entrar em tela cheia:** usa a Fullscreen API; a apresentação continua em janela se o navegador bloquear.
- **Cronômetro:** informativo, sem limite. **Reiniciar aula:** limpa resultados temporários e retorna à primeira etapa.

A etapa atual, o cronômetro e os resultados sintéticos da aula são armazenados apenas no `sessionStorage` para resistir a um refresh. Mudanças de tela não são registradas no histórico geral. As análises executadas pelos botões reais continuam sujeitas ao registro educacional já implementado nos módulos.

## Demonstrações

`GET /api/classroom/scenarios` seleciona referências fictícias presentes no banco, com fallback para o primeiro registro. A etapa de Fisioterapia prefere, entre uma amostra pequena, probabilidades menos extremas para facilitar discussão. Todos os cálculos e previsões utilizam as APIs especializadas existentes.

Na etapa de visão computacional, o componente de pose carrega apenas quando essa tela é aberta. A permissão da câmera é pedida somente depois do clique em **Abrir câmera**. Frames não são enviados ao backend. A tentativa possui tempo limite com mensagem amigável. **Usar demonstração visual** mostra um esquema estático rotulado; não simula uma webcam ativa. Ao trocar de etapa, os tracks da câmera são encerrados. Ângulos 2D e contagem são métricas matemáticas aproximadas, sem interpretação clínica.

Na etapa generativa, a explicação utiliza a previsão real já executada na aula. Sem chave externa, o provider local determinístico permanece disponível. O texto gerado não altera números nem recalcula previsões.

Os links **Abrir demonstração completa** levam ao módulo correspondente com um botão **Voltar à apresentação** que preserva a etapa. A aula não cria modelos novos e não representa avaliação clínica.

## Roteiro de revisão para aluno iniciante

Consulte [roteiro manual de teste](classroom-beginner-qa.md) para percorrer todas as etapas e verificar botões, resultados, glossário, modo aluno, modo professor e limites das demonstrações.
