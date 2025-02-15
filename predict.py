# predict.py
# Prediction interface for Cog ⚙️
# https://github.com/replicate/cog/blob/main/docs/python.md

from cog import BasePredictor, Input, Path
import matchering as mg


class Predictor(BasePredictor):
    def predict(
        self,
        target: Path = Input(description="Target audio file path"),
        reference: Path = Input(description="Reference audio file path"),
    ) -> Path:
        mg.log(warning_handler=print)

        mg.process(
            target=target,
            reference=reference,
            results=[
                mg.pcm16("/tmp/remastered_16bit.wav"),
            ],
        )

        return Path("/tmp/remastered_16bit.wav")
