# Usa uma imagem base Python leve
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os outros arquivos do diretório atual para o diretório de trabalho no contêiner
COPY . .

# Comando para executar a aplicação quando o contêiner iniciar
CMD ["python", "agent.py"]