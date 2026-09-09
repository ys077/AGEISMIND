import os
import json
import joblib
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_PATH = MODEL_DIR / "withdrawal_model_v1.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata_v1.json"

class ModelLoader:
    _instance = None
    _model = None
    _metadata = None
    _is_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance

    def load_model(self) -> Tuple[Any, Dict[str, Any]]:
        """Loads model and metadata. Caches it after first load."""
        if not self._is_loaded:
            if not MODEL_PATH.exists() or not METADATA_PATH.exists():
                raise FileNotFoundError("Model artifacts not found. Please train the model first.")
            
            self._model = joblib.load(MODEL_PATH)
            
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
                
            self._is_loaded = True
            
        return self._model, self._metadata

    def get_model(self) -> Any:
        model, _ = self.load_model()
        return model

    def get_metadata(self) -> Dict[str, Any]:
        _, metadata = self.load_model()
        return metadata

    def reload(self):
        """Forces reload of model from disk."""
        self._is_loaded = False
        self.load_model()

model_loader = ModelLoader()
