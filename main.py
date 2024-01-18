from deep_translator import GoogleTranslator

import argparse
import json
import subprocess
import os

import whisper

def argparser():
    parser = argparse.ArgumentParser(description="LoRA or QLoRA finetuning.")
    parser.add_argument(
        "--model",
        default="mlx-large",
        type=str,
        help="Path the the Whisper mlx model weights",
    )
    parser.add_argument(
        "--file",
        required=True,
        type=str,
        help="The file to generate subtitles on",
    )
    parser.add_argument(
        "--input-language",
        type=str,
        default="en",
        help="The language of the input video",
    )
    parser.add_argument(
        "--output-language",
        type=str,
        default=None,
        help="The language of the subtitles. None if the subtitles should not be translated",
    )
    parser.add_argument(
        "--burn",
        action='store_true',
        help="Burn the subtitles in the video."
    )

    return parser


# Formats a floating point number into HH:MM:SS,MS format used for srt files.
def formatTime(time):
    h = int(time // 3600)
    m = int((time % 3600) // 60)
    s = int(time % 60)
    ms = int((time - int(time)) * 1000)

    formatted = "{:02d}:{:02d}:{:02d},{:03d}".format(h, m, s, ms)

    return formatted


class Subber:
    def __init__(self, model, file, inputLanguage, outputLanguage):
        self.model = model
        self.inputFilePath = file
        self.inputLanguage = inputLanguage
        self.outputLanguage = outputLanguage
        self.subtitlePath = f"{self.outputLanguage}_{self.inputFilePath}.srt"

    def _transcribe(self):
        if os.path.exists(f"{self.inputFilePath}_transcription.txt"):
            print("Transcription file found.")
            with open(f"{self.inputFilePath}_transcription.txt", "r") as f:
                self.transcription = json.load(f)
            return
        print("Transcribing.")
        self.transcription = whisper.transcribe(self.inputFilePath, path_or_hf_repo=self.model)
        with open(f"{self.inputFilePath}_transcription.txt", "w+") as f:
            json.dump(self.transcription, f)

    def _translate(self):
        # Need to test fully
        # If no translation is needed
        if not self.outputLanguage:
            self.translatedSubs = self.transcription["segments"]
            self.subtitlePath = f"{self.inputLanguage}_{self.inputFilePath}.srt"
            return
        print("Translating.")
        self.translatedSubs = []
        for part in self.transcription["segments"]:
            translatedPart = {}
            translatedPart["start"] = part["start"]
            translatedPart["end"] = part["end"]
            translatedPart["text"] = GoogleTranslator(source=self.inputLanguage, target=self.outputLanguage).translate(part["text"])
            self.translatedSubs.append(translatedPart)

    def _create_subtitles(self):
        with open(self.subtitlePath, "w+") as f:
            for i, part in enumerate(self.translatedSubs):
                start = formatTime(part['start'])
                end = formatTime(part['end'])
                text = part['text']
                f.write(f"{i}\n{start} --> {end}\n")
                f.write(f"{text}\n\n")

    def _burnSubtitles(self):
        print("Burning subtitles.")
        style = "Fontname=Roboto,OutlineColour=&H40000000,BorderStyle=3,ScaleY=0.87, ScaleX=0.87,Fontsize=15"
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                self.inputFilePath,
                "-vf",
                f"subtitles='{self.subtitlePath}':force_style='{style}'",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-c:a",
                "copy",
                f"{self.outputLanguage}_{self.inputFilePath}",
            ],
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL
        )

    def run(self, burn):
        if not os.path.exists(self.subtitlePath):
            self._transcribe()
            self._translate()
            self._create_subtitles()
        else:
            print("Subtitle file found.")
        if burn:
            self._burnSubtitles()


if __name__ == "__main__":
    parser = argparser()
    args = parser.parse_args()

    s = Subber(args.model, args.file, args.input_language, args.output_language)
    s.run(args.burn)