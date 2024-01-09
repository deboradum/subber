from deep_translator import GoogleTranslator
from subprocess import run

import argparse
import whisper

def argparser():
    parser = argparse.ArgumentParser(description="LoRA or QLoRA finetuning.")
    parser.add_argument(
        "--file",
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
        default="en",
        help="The language of the subtitles",
    )
    parser.add_argument("--seed", type=int, default=0, help="The PRNG seed")
    return parser

class Subber:
    def __init__(self, file, inputLanguage, outputLanguage):
        self.inputFilePath = file
        self.inputLanguage = inputLanguage
        self.outputLanguage = outputLanguage

    def _transcribe(self):
        print("Transcribing.")
        self.transcription = whisper.transcribe(self.inputFilePath, word_timestamps=True)

    def _translate(self):
        print("Translating.")
        self.translatedSubs = {}
        for part in self.transcription["segments"]:
            translated = GoogleTranslator(source=self.inputFilePath, target=self.outputLanguage).translate(part["words"])
            self.translatedSubs["time"] = part["time"]
            self.translatedSubs["words"] = translated

    def _create_subtitles(self):
        # TODO
        self.subtitlePath = f"{self.inputFilePath}.vtt"
        with open(self.subtitlePath, "w+") as f:
            f.write()
            f.write()
            f.write("\n")

    def _burnSubtitles(self):
        print("Burning subtitles.")
        style = "Fontname=Roboto,OutlineColour=&H40000000,BorderStyle=3,ScaleY=0.87, ScaleX=0.87,Fontsize=15"
        # TODO: check args
        process_result = run(

        )

    def run(self):
        self._transcribe()
        self._translate()
        self._create_subtitles()
        self._burnSubtitles()


if __name__ == "__main__":
    parser = argparser()
    args = parser.parse_args()

    s = Subber(args.file, args.language)
    s.run()
