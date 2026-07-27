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
    """
    Configure pytest to use ExamplesDeployment for ManagerWorker tests.

    This sets the deployment path and config to point to ExamplesDeployment,
    since ManagerWorker is a subtopology within that deployment.
    """
    # Path: .../ManagerWorker/Subtopology/test/int/conftest.py -> go up to FlightExamples
    flight_examples = Path(__file__).parents[4]

    if not config.option.deployment_config:
        # Point to ExamplesDeployment's configuration
        config_path = flight_examples / "ExamplesDeployment" / "test" / "int" / "int_config.json"

        if config_path.exists():
            config.option.deployment_config = config_path

    if not config.option.deployment:
        # Point to ExamplesDeployment build artifacts
        # Use CI artifact structure: <platform>-artifacts/ExamplesDeployment at repo root
        repo_root = flight_examples.parent

        # Try common platform artifact locations for the deployment
        possible_builds = [
            repo_root / "aarch64-linux-artifacts" / "ExamplesDeployment",
            repo_root / "Darwin-artifacts" / "ExamplesDeployment",
            repo_root / "Linux-artifacts" / "ExamplesDeployment",
        ]

        for build_path in possible_builds:
            if build_path.exists() and (build_path / "bin").exists():
                config.option.deployment = build_path
                # Also set the dictionary path to ExamplesDeployment
                dict_file = build_path / "ExamplesDeploymentAppDictionary.xml"
                if dict_file.exists() and not config.option.dictionary:
                    config.option.dictionary = str(dict_file)
                break
        else:
            # If no build found, provide helpful error message
            pytest.exit(
                f"ExamplesDeployment build not found in artifact directories.\n"
                f"Searched: {[str(p) for p in possible_builds]}\n"
                f"Please build ExamplesDeployment before running integration tests."
            )
