# Base Image Build Process

This directory contains a multi-stage Docker build setup to optimize build times by separating slow-building dependencies (QuantLib, ORE) from application code.

## Structure

- **Dockerfile.base**: Builds base image with QuantLib, OpenSourceRiskEngine, Python 3.11, Boost, SWIG, and ODBC drivers
- **Dockerfile**: Main application image that uses the base image and only builds QLD libraries
- **Dockerfile.prod**: Production version that uses the base image and builds optimized QLD libraries

## Build Process

### 1. Build Base Image (Run Once or When Dependencies Change)

```bash
# Linux/macOS
./build-base.sh

# Windows
build-base.bat
```

This creates the `deval2-base:latest` image containing:
- Python 3.11.9 compiled from source
- Boost 1.84.0
- SWIG 4.2.0
- QuantLib (built from source)
- QuantLib-SWIG Python bindings
- OpenSourceRiskEngine (ORE)
- MS SQL Server ODBC drivers

### 2. Build Application Image

```bash
# Development
docker build -f Dockerfile -t deval2-app:dev .

# Production
docker build -f Dockerfile.prod -t deval2-app:prod .
```

The application images only build:
- QLD libraries and SWIG bindings
- Python application dependencies
- Application runtime setup

## Benefits

- **Faster rebuilds**: QuantLib/ORE only rebuild when their source changes
- **Layer caching**: Docker can cache the expensive base image layers
- **Cleaner separation**: Dependencies vs application code
- **Registry optimization**: Base image can be pushed to registry once and reused

## Registry Usage

To push the base image to a registry:

```bash
# Set registry URL
export REGISTRY_URL=your-registry.com/your-org

# Build and push base image
./build-base.sh

# Update Dockerfiles to reference registry image
# Change: FROM deval2-base:latest
# To:     FROM your-registry.com/your-org/deval2-base:latest
```

## Maintenance

- **Rebuild base image** when:
  - QuantLib source code changes
  - ORE source code changes
  - Python version needs updating
  - System dependencies change

- **Regular application builds** only rebuild:
  - QLD source code changes
  - Application code changes
  - Python requirements changes

## Troubleshooting

If builds fail:

1. Ensure base image exists: `docker images | grep deval2-base`
2. Rebuild base image if missing: `./build-base.sh`
3. Check Docker has enough disk space and memory
4. Verify QuantLib/ORE source files are present in `ql_build/` directory