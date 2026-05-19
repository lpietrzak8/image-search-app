import sys
import os
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

_transformers_mock = MagicMock()
_transformers_mock.CLIPModel = MagicMock()
_transformers_mock.CLIPProcessor = MagicMock()
_transformers_mock.AutoModel = MagicMock()
sys.modules.setdefault('transformers', _transformers_mock)

_peft_mock = MagicMock()
sys.modules.setdefault('peft', _peft_mock)
sys.modules.setdefault('peft.tuners', _peft_mock)

_model_mock = MagicMock()
_model_mock.ClipModel = MagicMock()
sys.modules.setdefault('model', _model_mock)

_original_makedirs = os.makedirs
def _safe_makedirs(path, *args, **kwargs):
    if str(path).startswith('/app'):
        return
    _original_makedirs(path, *args, **kwargs)
os.makedirs = _safe_makedirs

import db_connector as _dbc
_dbc.DB_PATH = os.path.join(tempfile.gettempdir(), "test_clip_service.db")
