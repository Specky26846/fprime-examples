"""
Configuration for ManagerWorker Subtopology integration tests.

ManagerWorker is a subtopology (not a standalone deployment) that is part of
ExamplesDeployment. These integration tests run against ExamplesDeployment
to access the ManagerWorker components.

Note: These tests require a running GDS server. In CI, this is handled by the
project-builder action. For local testing, start the GDS first:
    fprime-gds -d FlightExamples/build-artifacts/<platform>/ExamplesDeployment
"""
from pathlib import Path
import pytest


def pytest_configure(config):

    # Path: .../ManagerWorker/Subtopology/test/int/conftest.py -> go up to FlightExamples
    # flight_examples = Path(__file__).parents[4]

    """
    Set default deployment configuration if not provided via command line.
    """
    if not config.option.deployment_config:
        # Set the path relative to this conftest.py file
        config_path = Path(__file__).parent / "int_config.json"
        config.option.deployment_config = config_path
