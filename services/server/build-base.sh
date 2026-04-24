#!/bin/bash

# Build script for the base image with QuantLib and ORE
# This should be run whenever QuantLib or ORE dependencies change

set -e

IMAGE_NAME="deval2-base"
IMAGE_TAG="latest"
REGISTRY_URL="${REGISTRY_URL:-}" # Optional: set to push to a registry

echo "Building base image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Build the base image
docker build \
    -f Dockerfile.base \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    .

echo "Base image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"

# Optional: Push to registry if REGISTRY_URL is set
if [ -n "$REGISTRY_URL" ]; then
    echo "Tagging image for registry: ${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"

    echo "Pushing to registry..."
    docker push "${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"

    echo "Image pushed successfully to registry"
fi

echo "Base image build complete!"
echo ""
echo "Usage:"
echo "  - The main Dockerfile now references '${IMAGE_NAME}:${IMAGE_TAG}'"
echo "  - Run this script whenever QuantLib/ORE sources change"
echo "  - Set REGISTRY_URL environment variable to push to a registry"