# Multi-stage build to reduce final image size
# Stage 1: Builder - Uses pre-built base image with QuantLib and ORE
FROM deval2-base:latest AS builder

# Set the work directory
WORKDIR /usr/src/app

# Base image already contains QLD libraries and Python bindings

# Install Python application dependencies
COPY requirements.txt /tmp/requirements.txt
RUN /usr/local/bin/python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade pip && \
    /usr/local/bin/python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt && \
    /usr/local/bin/python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org debugpy==1.8.5 werkzeug==2.2.2 && \
    rm /tmp/requirements.txt

# Stage 2: Runtime - Minimal runtime environment
FROM registry.access.redhat.com/ubi9/ubi-minimal AS runtime

# Set work directory
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH:/opt/mssql-tools18/bin"
ENV LD_LIBRARY_PATH="/usr/local/lib"
ENV PKG_CONFIG_PATH="/usr/local/lib/pkgconfig"
ENV BOOST_ROOT=/usr/local

# Install minimal runtime dependencies
RUN echo "sslverify=false" >> /etc/dnf/dnf.conf && \
    microdnf update -y && \
    microdnf install -y \
      openssl \
      bzip2 \
      zlib \
      sqlite \
      libffi \
      pam \
      libstdc++ \
      libgcc && \
    microdnf clean all

# Copy Python installation from builder
COPY --from=builder /usr/local /usr/local

# Copy ODBC drivers and MS SQL tools from builder
COPY --from=builder /opt/mssql-tools18 /opt/mssql-tools18
COPY --from=builder /etc/pki/rpm-gpg /etc/pki/rpm-gpg
COPY --from=builder /etc/yum.repos.d/mssql-release.repo /etc/yum.repos.d/mssql-release.repo

# Install ODBC drivers in runtime stage
RUN echo "sslverify=false" >> /etc/dnf/dnf.conf && \
    microdnf update -y && \
    ACCEPT_EULA=Y microdnf install -y msodbcsql18 && \
    microdnf clean all

# Create the app user and set up permissions
RUN groupadd --system app && useradd --system --home /usr/src/app --no-create-home --gid app app && \
    mkdir -p /home/app /var/lib/app_data /var/log/gunicorn && \
    chown -R app:app /usr/src/app /var/log/gunicorn /var/lib/app_data /home/app && \
    chmod -R 775 /usr/src/app /var/log/gunicorn /var/lib/app_data /home/app

# Copy project files
COPY manage.py /usr/src/app/
COPY requirements.txt /usr/src/app/
COPY migrations/ /usr/src/app/migrations/
COPY project/ /usr/src/app/project/

# Copy pyarmor runtime if exists
COPY pyarmor_runtime_00640[2]/ /usr/src/app/pyarmor_runtime_006402/

# Copy QLD Python bindings from builder to the correct location in project
# RUN mkdir -p /usr/src/app/project/qld/engine/qld/
# COPY --from=builder /usr/local/lib/python3.11/site-packages/qld/ /usr/src/app/project/qld/engine/qld/

# Copy configuration and entrypoint
COPY gunicorn_config.py /usr/src/app/
COPY entrypoint.sh /usr/src/app/
RUN chmod +x /usr/src/app/entrypoint.sh

# Change ownership to the app user
RUN chown -R app:app /usr/src/app/

# Switch to the app user
USER app

# Run entrypoint
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]