# Roteiro de teste — aluno sem experiência em IA

Abra `/aula` em uma janela nova. Escolha **Explorar sozinho**. Não use o menu lateral nem leia documentação externa. Em cada etapa, confirme que a pergunta inicial, a explicação simples e o próximo clique estão claros. Use **Glossário** quando encontrar uma palavra desconhecida; a rota `/aula/glossario` deve abrir diretamente e retornar à etapa anterior.

## Percurso conceitual

1. Percorra as etapas 1–10 com **Próximo** e **Anterior**. Confira se dado, conjunto de dados, aprendizado, treino, teste, características e resposta esperada aparecem antes da primeira previsão.
2. Use **?** em Machine Learning, Dataset, Feature e Target. Abra **Quero saber mais** apenas se desejar detalhes.
3. Na etapa de acurácia, confira os 85 acertos e 15 erros do exemplo ilustrativo. Revele por que 90% pode esconder uma categoria nunca encontrada.
4. Leia Precision, Recall e F1 sem fórmulas. Abra os detalhes opcionais para ver fórmulas. Na matriz de confusão, clique em **Destacar acertos**, **Destacar erros** e **Mostrar todos**.

## Laboratórios

5. Em Fisioterapia, observe os dados antes de **Executar IA**. Confira três probabilidades reais. Revele que a maior barra não é certeza.
6. Clique em **Testar cenário**, altere uma única variável, **Aplicar cenário**, **Recalcular** e **Restaurar**. Confira antes/depois e o aviso de não causalidade. Na próxima etapa, **Mostrar fatores** deve exibir três características.
7. Em Enfermagem, revele o número diferente e clique em **Analisar anomalia**. A resposta deve falar em padrão aprendido, sem diagnóstico.
8. Em Farmácia, execute **classificação** e **regressão**. Compare uma categoria com um número. Em Veterinária, execute a classificação de um animal fictício.
9. No NLP, apague o texto: **Analisar texto** deve ficar desabilitado. Clique em **Carregar exemplo NLP**, **Analisar texto**, **Mostrar processamento**, **Ver todas as categorias** e **Buscar similares**. Confira tokens, stopwords removidas, pesos TF-IDF, temas e trechos semelhantes. Na etapa seguinte, **Mostrar clusters** deve exibir grupos e termos reais.
10. Em Visão Computacional, leia o fluxo pontos → matemática → lógica. Clique em **Abrir câmera** somente em ambiente autorizado; confirme overlay, coordenadas, ângulos e contador se houver dispositivo e corpo no enquadramento. Clique em **Fechar câmera** e confira que o indicador do dispositivo desligou. Sem câmera, aguarde a mensagem de tempo limite e use **Usar demonstração visual**: o esquema deve dizer que a webcam está desativada. A atividade de três ciclos depende de movimentos visíveis pelo modelo.
11. No construtor de prompts, altere um campo e confira o prompt gerado. Clique em **Copiar prompt** e veja o retorno. Em modo offline, **Executar prompt** deve estar desabilitado com explicação. Na etapa seguinte, **Explicar com IA** deve usar o resultado real de Fisioterapia e mostrar o modo local.

## Navegação e apresentação

12. Teste **Revelar resposta**, **Etapas**, **Notas**, **Reiniciar aula**, setas, espaço fora dos campos de texto, tela cheia e Esc. O espaço dentro de textarea não deve trocar de etapa.
13. Troque entre **Modo Aluno** e **Modo Professor**. O primeiro deve mostrar instruções adicionais; o segundo deve ser mais compacto.
14. Abra um módulo completo e use **Voltar à apresentação**. Atualize `/aula?step=psychology` diretamente. A etapa e os resultados temporários devem permanecer na mesma aba.
15. Confira o console do frontend e os logs do backend. Nenhuma troca de etapa deve criar um item no histórico. Somente as análises realmente executadas podem gerar metadados de histórico.

Todos os resultados são sintéticos e educacionais. A webcam depende de permissão, dispositivo e enquadramento; o esquema estático nunca deve ser apresentado como vídeo ao vivo.
