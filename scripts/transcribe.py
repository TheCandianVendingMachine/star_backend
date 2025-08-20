import sys
import whisperx
import torch
import gc
import contextlib
from pathlib import Path
from star.environment import ENVIRONMENT
from star.configuration import Configuration


@contextlib.contextmanager
def resource_cleaner(*objs_to_clean):
    yield
    gc.collect()
    torch.cuda.empty_cache()
    for obj in objs_to_clean:
        del obj


class Transcriber:
    audio_path: Path
    subtitle_path: Path
    model_path: Path

    model_variant: str
    compute_type: str
    device: str
    batch_size: int

    def __init__(self, audio_path: Path):
        config = Configuration('transcription.env')
        self.compute_type = config.require('compute_type').get()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model_variant = config.require('model_variant').get()
        self.batch_size = int(config.require('batch_size').get())

        self.audio_path = audio_path
        self.subtitle_path = self.audio_path.with_suffix('.srt')
        self.model_path = ENVIRONMENT.model_folder() / 'whisperx' / self.model_variant / self.compute_type

        print(f'Using whisperx.{self.model_variant}.{self.compute_type} on {self.device} with {self.batch_size} batch size')
        self.model = whisperx.load_model(
            self.model_variant, self.device, compute_type=self.compute_type, download_root=self.model_path
        )

    def transcribe(self):
        print(f'Loading {self.audio_path}')
        with resource_cleaner(self.model):
            audio = whisperx.load_audio(self.audio_path)
            result = self.model.transcribe(audio, batch_size=self.batch_size)

        print('Aligning transcription output')
        model, metadata = whisperx.load_align_model(language_code='en', device=self.device, model_dir=self.model_path)
        with resource_cleaner(model):
            result = whisperx.align(result['segments'], model, metadata, audio, self.device, return_char_alignments=False)

        print(f'Writing transcription to {self.subtitle_path}')
        with open(self.subtitle_path, 'w') as f:

            def timecode(seconds) -> tuple[int, int, int, int]:
                return (int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60), int(seconds * 1000) % 1000)

            for idx, segment in enumerate(result['segments']):
                start = segment['start']
                end = segment['end']
                sentence = segment['text']

                start_hour, start_minute, start_second, start_millisecond = timecode(start)
                end_hour, end_minute, end_second, end_millisecond = timecode(end)

                start_timecode = f'{start_hour:02}:{start_minute:02}:{start_second:02},{start_millisecond:03}'
                end_timecode = f'{end_hour:02}:{end_minute:02}:{end_second:02},{end_millisecond:03}'

                f.write(f'{idx + 1}\n{start_timecode} --> {end_timecode}\n{sentence}\n\n')


def transcribe(audio_path: Path | str):
    if isinstance(audio_path, str):
        audio_path = Path(audio_path)
    Transcriber(audio_path).transcribe()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('No file supplied')
    else:
        transcribe(Path(sys.argv[1]))
