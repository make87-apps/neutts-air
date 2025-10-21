from huggingface_hub import snapshot_download


def main():
    repos = [
        "neuphonic/neutts-air-q4-gguf",
        "neuphonic/neucodec-onnx-decoder",
    ]
    for repo in repos:
        print(f"Downloading {repo} into default cache ...")
        snapshot_download(repo_id=repo)
    print("Downloads complete.")
