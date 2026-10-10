import base64
import io

import numpy as np
from PIL import Image
from deepface import DeepFace


def _b64_to_array(b64: str) -> np.ndarray:
    padding = (4 - len(b64) % 4) % 4
    img_bytes = base64.b64decode(b64 + "=" * padding)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return np.array(img)


def compare_faces(ref_b64: str, probe_b64: str) -> tuple[bool, float]:
    img_ref = _b64_to_array(ref_b64)
    img_probe = _b64_to_array(probe_b64)

    result = DeepFace.verify(
        img1_path=img_ref,
        img2_path=img_probe,
        model_name="Facenet",
        enforce_detection=False,
        detector_backend="opencv",
        threshold=2.99,
    )
    verified  = result["verified"]
    distance  = round(result["distance"], 4)
    threshold = result.get("threshold", 0.8)
    diff      = round(distance - threshold, 4)
    estado    = f"SUPERÓ por {diff}" if diff > 0 else f"por debajo por {abs(diff)}"
    print(f"[*] Biométrico — verified: {verified} | distance: {distance} | threshold: {threshold} | {estado}")
    return verified, distance
