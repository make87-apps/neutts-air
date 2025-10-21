import os
from huggingface_hub import snapshot_download


def main():
    # GGUF backbone (smallest, fastest)
    model_repo = "neuphonic/neutts-air-q4-gguf"
    codec_repo = "neuphonic/neucodec-onnx-decoder"

    base_dir = "/models"
    os.makedirs(base_dir, exist_ok=True)

    print(f"Downloading {model_repo}...")
    snapshot_download(repo_id=model_repo, local_dir=os.path.join(base_dir, "backbone"))

    print(f"Downloading {codec_repo}...")
    snapshot_download(repo_id=codec_repo, local_dir=os.path.join(base_dir, "codec"))

    print("Downloads complete.")


if __name__ == "__main__":
    main()
