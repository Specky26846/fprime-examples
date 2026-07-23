"""
Configuration for ExamplesDeployment integration tests.
This conftest.py file provides the deployment configuration path to pytest.
"""
from pathlib import Path
import pytest


def pytest_configure(config):
    """
    Set default deployment configuration if not provided via command line.
    """
    if not config.option.deployment_config:
        # Set the path relative to this conftest.py file
        config_path = Path(__file__).parent / "int_config.json"
        config.option.deployment_config = config_path
