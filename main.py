from deep_translator import GoogleTranslator
from tqdm import tqdm

import argparse
import json
import subprocess
import os
import mlx_whisper

import t5

language_map = {
    "ja": "Japanese",
    "en": "English",
    "nl": "Dutch",
}

def argparser():
    parser = argparse.ArgumentParser(description="Transcribe and translate videos using MLX whisper and T5.")
    parser.add_argument(
        "--w-model",
        default="whisper-q-mlx-large",
        type=str,
        help="Path the the Whisper mlx model weights",
    )
    parser.add_argument(
        "--t-model",
        default="t5-large",
        type=str,
        help="Path the the FLAN-T5 mlx model weights",
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
        help="The language of the input video. 'ja' for Japanese, 'en' for English, 'nl' for Dutch.",
    )
    parser.add_argument(
        "--output-language",
        type=str,
        default=None,
        help="The language of the subtitles. None if the subtitles should not be translated",
    )
    # Note that some languages such as Japanese are not supported by FLAN-T5.
    parser.add_argument(
        "--local-translate",
        action='store_true',
        help="Translate locally using Google's FAN-T5",
    )
    parser.add_argument(
        "--burn",
        action='store_true',
        help="Burn the subtitles in the video."
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="The name of the burned output video"
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
    def __init__(self):
        self.w_model = args.w_model
        self.t5_model = args.t_model
        self.inputFilePath = args.file
        self.inputLanguage = args.input_language
        self.outputLanguage = args.output_language

        self.subtitlePath = f"{self.inputFilePath}_{self.outputLanguage}.srt"
        self.transcriptPath = f"{self.inputFilePath}_transcription.txt"

    def _transcribe(self):
        if os.path.exists(self.transcriptPath):
            print("Transcription file found.")
            with open(self.transcriptPath, "r", encoding="utf-8") as f:
                self.transcription = json.load(f)
            return
        print("Transcribing.")
        self.transcription = mlx_whisper.transcribe(
            self.inputFilePath,
            path_or_hf_repo=self.w_model,
            verbose=False,
            **{"language": self.inputLanguage, "task": "transcribe"}
        )
        with open(self.transcriptPath, "w", encoding="utf-8") as f:
            json.dump(self.transcription, f, ensure_ascii=False, indent=2)

    def _translate(self):
        # If only subbing and no translation is needed
        if not self.outputLanguage:
            self.translatedSubs = self.transcription["segments"]
            self.subtitlePath = f"{self.inputFilePath}_{self.inputLanguage}.srt"
            return
        print("Translating.")
        if args.local_translate:
            self._translate_local()
        else:
            self._translate_google()

    # Translating using Google Translate api.
    def _translate_google(self):
        self.translatedSubs = []
        for part in tqdm(self.transcription["segments"]):
            translatedPart = {}
            translatedPart["start"] = part["start"]
            translatedPart["end"] = part["end"]
            translatedPart["text"] = GoogleTranslator(source=self.inputLanguage, target=self.outputLanguage).translate(part["text"])
            self.translatedSubs.append(translatedPart)

    # Translating using a local FAN-T5 model.
    def _translate_local(self):
        self.translatedSubs = []
        model, tokenizer = t5.load_model(self.t5_model, "bfloat16")

        inp_lang = language_map[self.inputLanguage]
        outp_lang = language_map[self.outputLanguage]
        for part in tqdm(self.transcription["segments"]):
            text = part["text"]

            # Run t5 inference.
            prompt = f"translate from {inp_lang} to {outp_lang}: {text}"
            print("\n", prompt)
            tokens = []
            for token, n_tokens in zip(
                t5.generate(prompt, model, tokenizer, 0.0), range(200)
            ):
                if token.item() == tokenizer.eos_id:
                    break
                print(
                    tokenizer.decode([token.item()], with_sep=n_tokens > 0),
                    end="",
                    flush=True,
                )
                tokens.append(token.item())

            translatedPart = {}
            translatedPart["start"] = part["start"]
            translatedPart["end"] = part["end"]
            translatedPart["text"] = tokenizer.decode(tokens)
            self.translatedSubs.append(translatedPart)

    def _create_subtitles(self):
        with open(self.subtitlePath, "w+") as f:
            for i, part in enumerate(self.translatedSubs):
                start = formatTime(part['start'])
                end = formatTime(part['end'])
                text = part['text']
                f.write(f"{i}\n{start} --> {end}\n")
                f.write(f"{text}\n\n")

    def _burnSubtitles(self, output_video):
        input_dir = os.path.dirname(self.inputFilePath)
        input_name = os.path.basename(self.inputFilePath)
        output_file = os.path.join(input_dir, f"{self.outputLanguage}_{input_name}")
        if os.path.exists(output_file):
            print("Burned video found.")
            return

        print("Burning subtitles.")
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-loglevel", "error",
                "-i", self.inputFilePath,
                "-vf", f"subtitles='{self.subtitlePath}':force_style='Fontname=Roboto,OutlineColour=&H40000000,BorderStyle=3,ScaleY=0.87,ScaleX=0.87,Fontsize=15'",
                "-c:v", "libx264",
                "-crf", "18",
                "-c:a", "copy",
                output_file
            ]
        )

    def run(self):
        if not os.path.exists(self.subtitlePath):
            self._transcribe()
            self._translate()
            self._create_subtitles()
        else:
            print("Subtitle file found.")
        if args.burn:
            self._burnSubtitles(args.out)


parser = argparser()
args = parser.parse_args()

if __name__ == "__main__":
    s = Subber()
    s.run()
