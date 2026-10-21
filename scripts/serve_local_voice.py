"""Start the downloaded Lisa Reichert voice on localhost only."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yml")
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--port", type=int, default=8095)
    args = parser.parse_args()

    cache = Path("D:/Caches/Yelena/xtts")
    for name, directory in {
        "HF_HOME": cache / "huggingface", "TORCH_HOME": cache / "torch",
        "XDG_CACHE_HOME": cache, "MPLCONFIGDIR": cache / "matplotlib",
        "NUMBA_CACHE_DIR": cache / "numba",
        "TTS_HOME": cache,
    }.items():
        os.environ[name] = str(directory)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TORCH_FORCE_WEIGHTS_ONLY_LOAD"] = "1"

    import uvicorn
    import yaml
    from src.xtts_server import LocalXTTS, create_app

    if args.model_dir is None:
        cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
        model_dir = cfg.get("tts", {}).get("xtts_service", {}).get("model_dir")
        if not model_dir:
            parser.error("Set tts.xtts_service.model_dir or pass --model-dir")
        args.model_dir = Path(model_dir)
    engine = LocalXTTS(args.model_dir, device=args.device)
    uvicorn.run(create_app(engine), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
