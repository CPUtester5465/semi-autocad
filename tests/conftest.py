"""Pytest configuration and shared fixtures."""

import pytest
import sys
from unittest.mock import MagicMock


def is_cq_electronics_available():
    """Check if cq_electronics is installed and importable."""
    try:
        import cq_electronics
        return True
    except ImportError:
        return False


# Skip marker for tests requiring cq_electronics
requires_cq_electronics = pytest.mark.skipif(
    not is_cq_electronics_available(),
    reason="cq_electronics not installed"
)


@pytest.fixture
def mock_cq_electronics(monkeypatch):
    """Mock cq_electronics for testing without the actual library installed."""
    import cadquery as cq

    # Create a mock cq_object that returns a simple box
    def make_mock_component(**kwargs):
        mock = MagicMock()
        # Create a real CadQuery workplane for testing
        mock.cq_object = cq.Workplane("XY").box(10, 10, 5)
        return mock

    # Mock the various cq_electronics modules
    mock_rpi3b = MagicMock()
    mock_rpi3b.RPi3b = make_mock_component

    mock_headers = MagicMock()
    mock_headers.PinHeader = make_mock_component

    mock_rj45 = MagicMock()
    mock_rj45.JackSurfaceMount = make_mock_component

    mock_bga = MagicMock()
    mock_bga.BGA = make_mock_component

    mock_din_clip = MagicMock()
    mock_din_clip.DinClip = make_mock_component

    mock_din_rail = MagicMock()
    mock_din_rail.TopHat = make_mock_component

    # P2.2: Add PiTrayClip mock
    mock_pitray_clip = MagicMock()
    mock_pitray_clip.PiTrayClip = make_mock_component

    # Insert mocks into sys.modules
    modules = {
        "cq_electronics": MagicMock(),
        "cq_electronics.rpi": MagicMock(),
        "cq_electronics.rpi.rpi3b": mock_rpi3b,
        "cq_electronics.connectors": MagicMock(),
        "cq_electronics.connectors.headers": mock_headers,
        "cq_electronics.connectors.rj45": mock_rj45,
        "cq_electronics.smd": MagicMock(),
        "cq_electronics.smd.bga": mock_bga,
        "cq_electronics.mechanical": MagicMock(),
        "cq_electronics.mechanical.din_clip": mock_din_clip,
        "cq_electronics.mechanical.din_rail": mock_din_rail,
        "cq_electronics.sourcekit": MagicMock(),
        "cq_electronics.sourcekit.pitray_clip": mock_pitray_clip,
    }

    for name, mock in modules.items():
        monkeypatch.setitem(sys.modules, name, mock)

    yield modules


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for exports."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def simple_workplane():
    """Create a simple CadQuery workplane for testing."""
    import cadquery as cq
    return cq.Workplane("XY").box(10, 10, 5)
