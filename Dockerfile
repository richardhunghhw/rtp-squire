# See https://containers.dev/guide/dockerfile
# https://hub.docker.com/_/microsoft-devcontainers-python
FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

ENV APP_HOME /app
WORKDIR ${APP_HOME}
COPY . ./

# Install python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Run the application
ENTRYPOINT [ "python3" ]
CMD ["main.py"]