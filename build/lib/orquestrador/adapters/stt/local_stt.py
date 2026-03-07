from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class LocalSTT:
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "Dependencia ausente para STT local. Instale: pip install '.[stt]'"
            ) from exc

        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe_array(self, audio: "np.ndarray", sample_rate: int, language: str = "pt") -> str:
        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError(
                "Dependencia ausente para STT local. Instale: pip install '.[stt]'"
            ) from exc

        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, audio, sample_rate)
            segments, _ = self._model.transcribe(
                tmp.name,
                language=language,
                vad_filter=True,
            )
            return " ".join(seg.text.strip() for seg in segments).strip()
