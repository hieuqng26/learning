@echo off
REM Build script for the base image with QuantLib and ORE (Windows version)
REM This should be run whenever QuantLib or ORE dependencies change

set IMAGE_NAME=deval2-base
set IMAGE_TAG=latest

echo Building base image: %IMAGE_NAME%:%IMAGE_TAG%

REM Build the base image
docker build ^
    -f Dockerfile.base ^
    -t %IMAGE_NAME%:%IMAGE_TAG% ^
    .

if %ERRORLEVEL% neq 0 (
    echo Error building base image
    exit /b 1
)

echo Base image built successfully: %IMAGE_NAME%:%IMAGE_TAG%

REM Optional: Push to registry if REGISTRY_URL is set
if defined REGISTRY_URL (
    echo Tagging image for registry: %REGISTRY_URL%/%IMAGE_NAME%:%IMAGE_TAG%
    docker tag %IMAGE_NAME%:%IMAGE_TAG% %REGISTRY_URL%/%IMAGE_NAME%:%IMAGE_TAG%

    echo Pushing to registry...
    docker push %REGISTRY_URL%/%IMAGE_NAME%:%IMAGE_TAG%

    if %ERRORLEVEL% neq 0 (
        echo Error pushing to registry
        exit /b 1
    )

    echo Image pushed successfully to registry
)

echo Base image build complete!
echo.
echo Usage:
echo   - The main Dockerfile now references '%IMAGE_NAME%:%IMAGE_TAG%'
echo   - Run this script whenever QuantLib/ORE sources change
echo   - Set REGISTRY_URL environment variable to push to a registry