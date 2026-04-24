#!/bin/sh

# Run the tests
pytest --cov=projects --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:/usr/src/app/htmlcov --cov-config=.coveragerc -v tests

# Keep the container running
# tail -f /dev/null