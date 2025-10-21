import logging
import time
import torch
import numpy as np
import soundfile as sf
import os
from make87_messages.audio.frame_pcm_s16le_pb2 import FramePcmS16le
from make87.encodings import ProtobufEncoder
from make87.interfaces.zenoh import ZenohInterface
from app.neutts import NeuTTSAir

logging.Formatter.converter = time.gmtime
logging.basicConfig(
    format="[%(asctime)sZ %(levelname)s  %(name)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S",
)


class NeuTTSToFramePcm:
    """TTS converter using NeuTTSAir, supporting both ONNX and GGUF models."""

    def __init__(
        self,
        backbone: str,
        ref_codes_path: str,
        ref_text: str,
        sample_rate: int = 24000,
    ):
        self.sample_rate = sample_rate
        self.backbone = backbone

        # Resolve reference text and codes
        if ref_text and os.path.exists(ref_text):
            with open(ref_text, "r") as f:
                ref_text = f.read().strip()
        self.ref_text = ref_text

        if ref_codes_path and os.path.exists(ref_codes_path):
            self.ref_codes = torch.load(ref_codes_path)
        else:
            self.ref_codes = None

        # Initialize NeuTTSAir model
        self.tts = NeuTTSAir(
            backbone_repo="neuphonic/neutts-air-q4-gguf",
            backbone_device="cpu",
            codec_repo="neuphonic/neucodec-onnx-decoder",
            codec_device="cpu",
        )

    def text_to_frames(self, text: str):
        """Generate audio chunks (as PCM S16LE bytes) from input text."""
        for chunk in self.tts.infer_stream(text, self.ref_codes, self.ref_text):
            audio = np.clip(chunk * 32767, -32768, 32767).astype(np.int16)
            yield audio.tobytes()

    def infer_stream(
        self, text: str, ref_codes: np.ndarray | torch.Tensor, ref_text: str
    ) -> Generator[np.ndarray, None, None]:
        try:
            yield from self.tts.infer_stream(text, ref_codes, ref_text)
        except Exception as e:
            print(f"Error during inference: {e}")

    def text_to_frame_pcm_s16le(self, text: str, pts_start: int = 0):
        """Convert text to FramePcmS16le messages preserving chunk timing."""
        pts = pts_start

        for pcm_chunk in self.infer_stream(text, self.ref_codes, self.ref_text):
            # Convert normalized float [-1,1] to 16-bit PCM
            audio = np.clip(pcm_chunk * 32767, -32768, 32767).astype(np.int16)
            pcm_bytes = audio.tobytes()

            # Estimate duration (in seconds) from sample count
            duration_s = len(audio) / self.sample_rate

            yield FramePcmS16le(
                data=pcm_bytes,
                pts=pts,
                time_base=FramePcmS16le.Fraction(num=1, den=self.sample_rate),
                channels=1,
            )

            pts += len(audio)
            # Optional: pacing to real-time for consumers
            time.sleep(duration_s)


def main():
    message_encoder = ProtobufEncoder(message_type=FramePcmS16le)
    zenoh_interface = ZenohInterface(name="zenoh")

    publisher = zenoh_interface.get_publisher("tts_audio")
    subscriber = zenoh_interface.get_subscriber("tts_text")

    # Configure TTS (change these paths/models to your actual ones)
    backbone = os.getenv("NEUTTS_BACKBONE", "neuphonic/neutts-air")
    ref_codes_path = os.getenv("NEUTTS_REF_CODES", "ref_codes.pt")
    ref_text = os.getenv("NEUTTS_REF_TEXT", "/app/reference_text.txt")

    converter = NeuTTSToFramePcm(
        backbone=backbone, ref_codes_path=ref_codes_path, ref_text=ref_text
    )

    for msg in subscriber:
        text = msg.payload.to_bytes().decode("utf-8").strip()
        test_filtered = text.replace("*", "").replace(":", ". ").replace("\n", ". ")
        sentences = [
            sentence.strip()
            for sentence in test_filtered.split(". ")
            if sentence.strip()
        ]
        for sentence in sentences:
            logging.info(f"Generating TTS for: {sentence}")

            for frame in converter.text_to_frame_pcm_s16le(sentence):
                encoded = message_encoder.encode(frame)
                publisher.put(payload=encoded)
                logging.debug(f"Published frame PTS={frame.pts}")

        logging.info(f"Done streaming: {text}")


if __name__ == "__main__":
    main()
