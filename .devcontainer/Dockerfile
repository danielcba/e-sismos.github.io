# Usa una imagen base de Ubuntu
FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu

# Instala PostgreSQL
RUN apt-get update && \
    apt-get install -y postgresql postgresql-contrib

# Expon el puerto 5432 de PostgreSQL
EXPOSE 5432

# Cambia la configuración de PostgreSQL para permitir conexiones externas
RUN sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/*/main/postgresql.conf && \
    echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/*/main/pg_hba.conf

# Configura el contenedor para iniciar PostgreSQL
CMD service postgresql start && tail -f /dev/null

