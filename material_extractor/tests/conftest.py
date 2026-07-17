"""Test configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_material_data():
    """Sample material data for testing."""
    return [
        {"material": "Copper (Cu)", "weight_mg": 1.5, "substance": "Cu"},
        {"material": "Nickel (Ni)", "weight_mg": 0.8, "substance": "Ni"},
        {"material": "Epoxy Resin", "weight_mg": 2.3, "substance": ""},
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory."""
    return tmp_path / "output"