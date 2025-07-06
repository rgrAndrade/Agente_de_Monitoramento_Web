import os
import time
import requests
import ping3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient

# --- Configurações do Banco de Dados MongoDB ---
# Obtém a URI do MongoDB das variáveis de ambiente ou usa um valor padrão
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/monitor_db")
client = MongoClient(MONGODB_URI)
db = client.get_database() # Conecta ao banco de dados especificado na URI (ex: monitor_db)
metrics_collection = db.metrics # Define a coleção onde as métricas serão armazenadas

# --- Funções de Teste de Rede ---
def run_ping_test(host):
    print(f"Running ping test for {host}...")
    try:
        # Realiza o ping e obtém o RTT em milissegundos
        delay = ping3.ping(host, unit='ms', timeout=1)
        
        # Prepara o documento de métrica para inserção no MongoDB
        metric_doc = {
            "timestamp": datetime.now(),
            "target": host,
            "metric_type": "ping",
        }

        if delay is not None:
            # Se o ping foi bem-sucedido
            loss = 0.0 # Consideramos 0% de perda se o ping retornou um valor
            status = 'success'
            metric_doc.update({
                "value": delay, # Valor do RTT
                "status": status,
                "packet_loss": loss
            })
            print(f"Ping to {host}: RTT={delay:.2f}ms, Packet Loss={loss}%")
        else:
            # Se o ping falhou (delay é None)
            delay = -1.0 # Valor para indicar falha
            loss = 100.0 # 100% de perda de pacotes
            status = 'failed'
            metric_doc.update({
                "value": delay,
                "status": status,
                "packet_loss": loss
            })
            print(f"Ping to {host}: Failed, Packet Loss={loss}%")
        
        # Insere o documento na coleção de métricas
        metrics_collection.insert_one(metric_doc)

    except Exception as e:
        # Captura e loga quaisquer erros durante o ping
        print(f"Error pinging {host}: {e}")
        metrics_collection.insert_one({
            "timestamp": datetime.now(),
            "target": host,
            "metric_type": "ping",
            "value": -1.0, # Indica falha
            "status": "error",
            "error_message": str(e)
        })

def run_http_test(url):
    print(f"Running HTTP test for {url}...")
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5) # Realiza a requisição HTTP
        load_time = (time.time() - start_time) * 1000 # Calcula o tempo de carregamento em milissegundos
        status_code = response.status_code # Obtém o código de status HTTP
        status = 'success' if 200 <= status_code < 400 else 'failed' # Determina o status geral
        print(f"HTTP test for {url}: Load Time={load_time:.2f}ms, Status Code={status_code}")

        # Insere o documento com as métricas HTTP
        metrics_collection.insert_one({
            "timestamp": datetime.now(),
            "target": url,
            "metric_type": "http_response",
            "load_time": load_time,
            "status_code": status_code,
            "status": status
        })
    except requests.exceptions.RequestException as e:
        # Captura e loga erros de requisição HTTP
        print(f"Error accessing {url}: {e}")
        metrics_collection.insert_one({
            "timestamp": datetime.now(),
            "target": url,
            "metric_type": "http_response",
            "load_time": -1.0, # Indica falha
            "status_code": 0, # Código de status 0 para falha de conexão
            "status": "failed",
            "error_message": str(e)
        })

# --- Agendador de Testes ---
def scheduled_tests():
    print(f"\n--- Running scheduled tests at {datetime.now()} ---")
    
    # Lista de hosts para testes de Ping
    run_ping_test("google.com")
    run_ping_test("rnp.br")

    # Lista de URLs para testes HTTP
    run_http_test("https://google.com")
    # Esta URL é especificamente para testar um código 404 (Not Found)
    run_http_test("youtube.com")
    run_http_test("https://rnp.br")
    
    print("--- Scheduled tests finished ---\n")

if __name__ == '__main__':
    print("Starting monitoring agent...")
    # Inicializa o agendador em segundo plano
    scheduler = BackgroundScheduler()
    # Adiciona a tarefa 'scheduled_tests' para rodar a cada 1 minuto
    scheduler.add_job(scheduled_tests, 'interval', minutes=1)
    scheduler.start()

    try:
        # Mantém o thread principal vivo para que o agendador continue rodando
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Desliga o agendador ao receber um sinal de interrupção (Ctrl+C)
        scheduler.shutdown()
        print("Monitoring agent stopped.")