from deep_translator import GoogleTranslator
from subprocess import run

import argparse
import os
from pprint import pprint

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
        default="nl",
        help="The language of the subtitles",
    )

    return parser


def formatTime(time):
    return


class Subber:
    def __init__(self, model, file, inputLanguage, outputLanguage):
        self.model = model
        self.inputFilePath = file
        self.inputLanguage = inputLanguage
        self.outputLanguage = outputLanguage
        self.subtitlePath = f"{self.outputLanguage}_{self.inputFilePath}.vtt"

    def _transcribe(self):
        print("Transcribing.")
        self.transcription = whisper.transcribe(self.inputFilePath, path_or_hf_repo=self.model)

    def _translate(self):
        print("Translating.")
        self.translatedSubs = []
        for part in self.transcription["segments"]:
            translated = GoogleTranslator(source=self.inputLanguage, target=self.outputLanguage).translate(part["text"])
            translatedPart = {}
            translatedPart["start"] = part["start"]
            translatedPart["end"] = part["end"]
            translatedPart["words"] = translated
            self.translatedSubs.append(part)

    def _create_subtitles(self):
        with open(self.subtitlePath, "w+") as f:
            for part in self.translatedSubs:
                start = part['start']
                end = part['end']
                text = part['text']
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n")

    def _burnSubtitles(self):
        print("Burning subtitles.")
        style = "Fontname=Roboto,OutlineColour=&H40000000,BorderStyle=3,ScaleY=0.87, ScaleX=0.87,Fontsize=15"
        # TODO: check args
        process_result = run(

        )

    def run(self):
        if not os.path.exists(self.subtitlePath):
            self._transcribe()
            self._translate()
            self._create_subtitles()
        else:
            print("Subtitle file found.")
        # self._burnSubtitles()


if __name__ == "__main__":
    parser = argparser()
    args = parser.parse_args()

    s = Subber(args.model, args.file, args.input_language, args.output_language)
    s.run()
    pprint(s.transcription)
