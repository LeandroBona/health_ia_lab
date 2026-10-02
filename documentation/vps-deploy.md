# Deploy em uma VPS Linux

O HealthAI Lab usa dois containers na mesma rede Docker: Nginx serve o frontend e encaminha `/api/*` ao FastAPI. Somente `127.0.0.1:8080` é publicado no host. O Nginx instalado na VPS recebe o domínio público e encaminha para essa porta. SQLite, datasets e modelos ficam no volume nomeado `health_ai_data`.

## Preparação

Instale Git, Docker Engine e o plugin Docker Compose v2 na VPS. Obtenha o projeto por `git clone` e execute os comandos abaixo na raiz do checkout:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Mantenha `VITE_API_URL=/api` e `CORS_ORIGINS=`. A chave `OPENAI_API_KEY` é opcional e só entra no container do backend; vazia, a aplicação utiliza o `LocalTemplateProvider`. Não coloque a chave em variável `VITE_*` nem em arquivos do frontend. Alterar `VITE_API_URL` exige reconstruir a imagem do frontend.

Na primeira inicialização, o backend aplica as migrations, gera os datasets sintéticos e treina os modelos ausentes. Isso pode levar alguns minutos. Os dados persistem no volume ao recriar containers. Nunca use `docker compose down -v` para parar a aplicação, pois esse comando remove o volume.

Se quiser levar o banco, datasets e modelos deste projeto para a VPS, transfira essas três fontes ao checkout da VPS, faça backup e execute **antes** do primeiro `up`:

```bash
docker compose --env-file .env.production build
docker compose --env-file .env.production run --rm --no-deps \
  -v "$PWD/backend/health_ai_lab.db:/seed/health_ai_lab.db:ro" \
  -v "$PWD/datasets:/seed/datasets:ro" \
  -v "$PWD/backend/models:/seed/models:ro" \
  backend sh -c 'mkdir -p /data/datasets /data/models && cp /seed/health_ai_lab.db /data/health_ai_lab.db && cp -a /seed/datasets/. /data/datasets/ && cp -a /seed/models/. /data/models/'
```

Confira a compatibilidade dos modelos salvos com a versão de scikit-learn instalada na imagem. Se um artefato for incompatível, o módulo sinalizará que precisa de novo treinamento; não substitua arquivos de um volume já em uso sem backup.

## Construir e iniciar

```bash
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d
docker compose --env-file .env.production ps
curl -f http://127.0.0.1:8080/api/health
```

O backend não publica a porta 8000 no host. O frontend publica apenas em loopback; antes de configurar o Nginx do servidor, a aplicação não fica acessível pela Internet. O frontend e a API usam o mesmo domínio. A regra interna de Nginx preserva o prefixo `/api` ao encaminhar ao FastAPI.

## Nginx do servidor

Configure HTTPS no Nginx da VPS com seu certificado e domínio. Exemplo do bloco `server` HTTPS (substitua `lab.exemplo.org` e os caminhos do certificado):

```nginx
server {
    listen 443 ssl;
    server_name lab.exemplo.org;
    ssl_certificate /etc/letsencrypt/live/lab.exemplo.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lab.exemplo.org/privkey.pem;

    client_max_body_size 25m;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

Redirecione HTTP para HTTPS no Nginx do servidor. HTTPS é necessário para `getUserMedia` da Visão Computacional em um domínio público. A webcam e os frames são processados no navegador; o servidor recebe apenas as métricas numéricas quando o usuário escolhe registrar uma sessão. Os assets locais do MediaPipe são servidos pelo frontend.

## Verificação

Depois que o backend estiver saudável, confira:

```bash
curl -f http://127.0.0.1:8080/api/health
curl -f http://127.0.0.1:8080/api/classroom/readiness
curl -f http://127.0.0.1:8080/api/classroom/scenarios
curl -f http://127.0.0.1:8080/api/psicologia/model
curl -f http://127.0.0.1:8080/api/generative/status
curl -I http://127.0.0.1:8080/aula
curl -I http://127.0.0.1:8080/psicologia/laboratorio
curl -I http://127.0.0.1:8080/visao-computacional/laboratorio
curl -I http://127.0.0.1:8080/mediapipe/pose_landmarker_lite.task
```

Abra também o Modo Aula, o laboratório NLP, o simulador de cenário de Fisioterapia, a IA Generativa e a Visão Computacional no navegador. Teste a permissão da webcam pelo domínio HTTPS. Teste um refresh direto em uma rota React, como `/aula` ou `/fisioterapia/pacientes/PAC-0001`. O healthcheck comprova que a API responde; as demonstrações interativas precisam dessa verificação no navegador.

## Parar, logs e atualização

```bash
docker compose --env-file .env.production down
docker compose --env-file .env.production logs -f --tail=100
./deploy.sh
```

`deploy.sh` exige um checkout Git, faz `git pull --ff-only`, reconstrói as imagens e executa `docker compose up -d`. O script não apaga o volume. Faça backup periódico do volume `health_ai_data`, especialmente do SQLite. Não execute múltiplas réplicas do backend com o mesmo arquivo SQLite nesta implantação didática.
