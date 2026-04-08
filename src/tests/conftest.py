"""pytest configuration and fixtures"""
import sys
from unittest.mock import MagicMock, create_autospec

# Mock pyfuse3 for Windows/test environments where it's not available
sys.modules['pyfuse3'] = MagicMock()
