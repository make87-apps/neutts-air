#!/usr/bin/env python3
import torch
from librosa import load
from neucodec import NeuCodec
import logging
import os

logging.basicConfig(
    format="[%(asctime)s %(levelname)s] %(message)s",
    level=logging.INFO,
)


def main():
    ref_audio = "/home/phillip/projects/neutts-air/voices/arnold/reference_audio.mp3"
    default_text = "/home/phillip/projects/neutts-air/voices/arnold/reference_text.txt"
    output_path = "/home/phillip/projects/neutts-air/voices/arnold/ref_codes.pt"

    if not os.path.exists(ref_audio):
        raise FileNotFoundError(f"Reference audio not found: {ref_audio}")

    logging.info(f"Encoding reference audio from {ref_audio}")

    # Initialize the codec
    codec = NeuCodec.from_pretrained("neuphonic/neucodec")
    codec.eval().to("cpu")

    # Load and encode reference audio
    wav, _ = load(ref_audio, sr=16000, mono=True)
    wav_tensor = torch.from_numpy(wav).float().unsqueeze(0).unsqueeze(0)  # [1, 1, T]
    ref_codes = codec.encode_code(audio_or_path=wav_tensor).squeeze(0).squeeze(0)

    # Save the codes
    torch.save(ref_codes, output_path)
    logging.info(f"Reference codes saved to {output_path}")


if __name__ == "__main__":
    main()
