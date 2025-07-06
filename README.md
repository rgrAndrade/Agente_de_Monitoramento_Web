# Monitoramento Web com Python, MongoDB e Grafana

## Visão Geral do Projeto

Este projeto demonstra a construção de umaa solução completa de monitoramento de rede e web, utilizando uma arquitetura baseada em contêineres e orquestrada com Docker Compose. O objetivo é criar um agente de monitoramento que realiza testes de conectividade (ping) e desempenho web (HTTP), armazena os resultados em um banco de dados NoSQL (MongoDB) e os visualiza através de dashboards interativos no Grafana.

Esta solução foi desenvolvida como parte de uma prova técnica para a vaga de DevOps em Redes, focando na Questão 1: "Agente de monitoramento web".

## High-Level Design (HLD)

A arquitetura da solução é modular, desacoplada e baseada em microsserviços em contêineres, promovendo escalabilidade, manutenibilidade e facilidade de deploy.

**Componentes Principais:**

1.  **Agente de Monitoramento (`app_monitor`):**
    * **Tecnologia:** Python
    * **Responsabilidade:** Executar testes de rede periodicamente.
        * **Ping:** Medir latência (RTT) e perda de pacotes (%).
            * Alvos: `google.com`, `rnp.br`
        * **HTTP:** Medir tempo de carregamento de páginas e códigos de retorno (200, 404, etc.).
            * Alvos: `https://google.com`, `youtube.com`, `https://rnp.br`
    * **Armazenamento:** Envia os resultados brutos para o MongoDB.
    * **Agendamento:** Utiliza `APScheduler` para rodar os testes a cada minuto.

2.  **Banco de Dados (`db_monitor`):**
    * **Tecnologia:** MongoDB (NoSQL, baseado em documentos)
    * **Responsabilidade:** Armazenar os dados de métricas coletados pelo agente. Escolha ideal para dados semi-estruturados e de alta taxa de escrita, comum em cenários de monitoramento. Os dados são armazenados na coleção `metrics`.

3.  **Visualização (`grafana`):**
    * **Tecnologia:** Grafana
    * **Responsabilidade:** Conectar-se ao MongoDB e apresentar as métricas de forma visual através de dashboards personalizados. Permite a detecção rápida de problemas e tendências de desempenho.

**Fluxo de Operação:**

1.  O contêiner `app_monitor` inicia e executa o script Python `agent.py`.
2.  O `agent.py`, via `APScheduler`, realiza testes de ping e HTTP nos alvos configurados a cada 1 minuto.
3.  Os resultados de cada teste (RTT, perda de pacotes, tempo de carregamento HTTP, código de status) são formatados como documentos JSON e inseridos na coleção `metrics` no `db_monitor` (MongoDB).
4.  O contêiner `grafana` inicia e, através de um plugin específico para MongoDB, se conecta ao `db_monitor`.
5.  Os dashboards configurados no Grafana consultam o MongoDB e exibem as métricas em tempo real, permitindo a análise do desempenho da rede e dos serviços web monitorados.

## Instruções de Execução

Siga os passos abaixo para levantar a solução em seu ambiente.

1.  **Clone este Repositório:**
    ```bash
    git clone git@github.com:rgrAndrade/Agente_de_Monitoramento_Web.git
    cd Agente_de_Monitoramento_Web
    ```

2.  **Verifique a Estrutura de Arquivos:**
    Certifique-se de que a estrutura de diretórios e arquivos esteja conforme o HLD e os snippets de código fornecidos.

    ```
    .
    ├── docker-compose.yml
    ├── monitor_agent/
    │   ├── Dockerfile
    │   ├── agent.py
    │   └── requirements.txt
    └── grafana_provisioning/
        └── datasources/
            └── mongodb_datasource.yml
    ```

3.  **Levantar os Contêineres:**
    No terminal, a partir do diretório raiz do projeto (onde está `docker-compose.yml`), execute o comando para construir as imagens e iniciar os serviços:

    ```bash
    docker compose up --build -d
    ```
    * `--build`: Garante que a imagem Docker do `app_monitor` seja construída (ou reconstruída se houver alterações) antes de iniciar o serviço.
    * `-d`: Executa os contêineres em modo *detached* (em segundo plano), liberando seu terminal.

    Aguarde alguns instantes para que todas as imagens sejam baixadas e os serviços iniciem. Você pode verificar o status dos contêineres com:
    ```bash
    docker compose ps
    ```
    Todos os serviços (`db_monitor`, `app_monitor`, `grafana`) devem estar com status `running`.

4.  **Verificar Logs do Agente de Monitoramento:**
    Para acompanhar a execução dos testes e a inserção de dados no MongoDB, você pode visualizar os logs do contêiner `app_monitor`:
    ```bash
    docker compose logs -f app_monitor
    ```
    Você deve ver mensagens indicando que os testes de ping e HTTP estão sendo realizados periodicamente (a cada minuto).

5.  **Acessar o Grafana:**
    Abra seu navegador web e navegue para:
    [http://localhost:3000](http://localhost:3000)

    * **Credenciais de Login:**
        * **Usuário:** `admin`
        * **Senha:** `admin_password` (É altamente recomendado alterar esta senha após o primeiro login em um ambiente de produção.)

6.  **Configurar os Dashboards no Grafana:**
    O *datasource* para o MongoDB já está provisionado automaticamente via `grafana_provisioning/datasources/mongodb_datasource.yml`.

    * No Grafana, vá para `Connections` (ou `Configuration` -> `Data sources`) no menu lateral para confirmar que `MongoDB_Monitor` está com status `OK`.

    * Crie um novo Dashboard clicando em `Dashboards` -> `New Dashboard` -> `Add new panel`.

    * Selecione o *datasource* `MongoDB_Monitor` e utilize as seguintes queries de exemplo (linguagem de query do MongoDB - MQL) para criar seus painéis:

    **Exemplos de Queries para Painéis:**

    * **Latência Média (Ping RTT) - google.com (Tipo: Graph/Time series)**
        ```json
        [
          { "$match": { "metric_type": "ping", "target": "google.com", "status": "success", "timestamp": { "$gte": "$__from", "$lt": "$__to" } } },
          { "$group": {
              "_id": { "$dateTrunc": { "date": "$timestamp", "unit": "minute" } },
              "avg_rtt": { "$avg": "$value" }
          }},
          { "$project": { "_id": 0, "time": "$_id", "value": "$avg_rtt" } },
          { "$sort": { "time": 1 } }
        ]
        ```

    * **Perda de Pacotes (%) - rnp.br (Tipo: Graph/Time series)**
        ```json
        [
          { "$match": { "metric_type": "ping", "target": "rnp.br", "timestamp": { "$gte": "$__from", "$lt": "$__to" } } },
          { "$group": {
              "_id": { "$dateTrunc": { "date": "$timestamp", "unit": "minute" } },
              "avg_packet_loss": { "$avg": "$packet_loss" }
          }},
          { "$project": { "_id": 0, "time": "$_id", "value": "$avg_packet_loss" } },
          { "$sort": { "time": 1 } }
        ]
        ```

    * **Tempo de Carregamento HTTP - google.com (Tipo: Graph/Time series)**
        ```json
        [
          { "$match": { "metric_type": "http_response", "target": "[https://google.com](https://google.com)", "status": "success", "timestamp": { "$gte": "$__from", "$lt": "$__to" } } },
          { "$group": {
              "_id": { "$dateTrunc": { "date": "$timestamp", "unit": "minute" } },
              "avg_load_time": { "$avg": "$load_time" }
          }},
          { "$project": { "_id": 0, "time": "$_id", "value": "$avg_load_time" } },
          { "$sort": { "time": 1 } }
        ]
        ```

    * **Códigos de Retorno HTTP - youtube.com (Tipo: Bar Chart/Pie Chart)**
        ```json
        [
          { "$match": { "metric_type": "http_response", "target": "youtube.com", "timestamp": { "$gte": "$__from", "$lt": "$__to" } } },
          { "$group": {
              "_id": "$status_code",
              "count": { "$sum": 1 }
          }},
          { "$project": { "_id": 0, "status_code": "$_id", "count": 1 } }
        ]
        ```

    * **Últimos Eventos de Monitoramento (Tipo: Table)**
        ```json
        [
          { "$match": { "timestamp": { "$gte": "$__from", "$lt": "$__to" } } },
          { "$sort": { "timestamp": -1 } },
          { "$limit": 20 }
        ]
        ```

    * **Salve o Dashboard** após adicionar e configurar seus painéis.