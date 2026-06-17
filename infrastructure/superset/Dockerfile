# Usa a imagem oficial do Apache Superset como base.
FROM apache/superset:latest

# Usa root apenas durante o build para instalar dependências no container.
USER root

# Instala pacotes necessários para compilar dependências Python e baixar o instalador do pip.
RUN apt-get update -y && \
    apt-get install -y gcc g++ libsasl2-dev build-essential python3-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instala o pip dentro do ambiente virtual usado pelo Superset.
RUN curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    /app/.venv/bin/python /tmp/get-pip.py && \
    rm /tmp/get-pip.py

# Instala o driver do Apache Druid com suporte ao SQLAlchemy no ambiente correto.
RUN /app/.venv/bin/python -m pip install --no-cache-dir "pydruid[sqlalchemy]==0.6.9"

# Copia o script de inicialização para dentro do container com o usuário correto.
COPY --chown=superset:superset superset-init.sh /app/superset-init.sh

# Permite que o script seja executado na inicialização do container.
RUN chmod +x /app/superset-init.sh

# Volta para o usuário padrão do Superset por segurança.
USER superset

# Executa o script de inicialização ao subir o container.
CMD ["/app/superset-init.sh"]