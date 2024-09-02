# subber
Transcribe and translate any video on MacBooks using MLX Whisper and T5.

# Usage
```
python main.py [-h] [--w-model W_MODEL] [--t-model T_MODEL] --file FILE [--input-language INPUT_LANGUAGE] [--output-language OUTPUT_LANGUAGE]
               [--local-translate] [--burn] [--out OUT]

Transcribe and translate videos using MLX whisper and T5.

options:
  -h, --help            show this help message and exit
  --w-model W_MODEL     Path the the Whisper mlx model weights
  --t-model T_MODEL     Path the the FLAN-T5 mlx model weights
  --file FILE           The file to generate subtitles on
  --input-language INPUT_LANGUAGE
                        The language of the input video. 'ja' for Japanese, 'en' for English, 'nl' for Dutch.
  --output-language OUTPUT_LANGUAGE
                        The language of the subtitles. None if the subtitles should not be translated
  --local-translate     Translate locally using Google's FAN-T5
  --burn                Burn the subtitles in the video.
  --out OUT             The name of the burned output video
```

Note that first a MLX Whisper model should be downloaded from the MLX Huggingface community. Any model (quantized or optimised in another way) should work without problem.
