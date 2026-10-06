import json
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from IndicTransToolkit import IndicProcessor


# ============================================================
# Configuration
# ============================================================

HOST = "127.0.0.1"
PORT = 8001

# Indic -> English (existing)
MODEL_NAME = "ai4bharat/indictrans2-indic-en-dist-200M"

# English -> Indic (new, for localized responses)
REVERSE_MODEL_NAME = "ai4bharat/indictrans2-en-indic-dist-200M"

LANGUAGE_CODES = {
    "Tamil": "tam_Taml",
    "Telugu": "tel_Telu",
    "Kannada": "kan_Knda",
    "Malayalam": "mal_Mlym",
    "Hindi": "hin_Deva",
}

ENGLISH_CODE = "eng_Latn"


# ============================================================
# Load IndicTrans2 (both directions)
# ============================================================

device = "cuda" if torch.cuda.is_available() else "cpu"


def _load(model_name: str):
    print(f"Loading IndicTrans2 model: {model_name}")

    tok = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
    )

    mdl = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        trust_remote_code=True,
    )

    mdl = mdl.to(device)
    mdl.eval()

    return tok, mdl


# Indic -> English
tokenizer, model = _load(MODEL_NAME)

# English -> Indic
reverse_tokenizer, reverse_model = _load(REVERSE_MODEL_NAME)

processor = IndicProcessor(inference=True)

print(f"IndicTrans2 (both directions) loaded on {device}")


# ============================================================
# Core translation
# ============================================================

def _run_translation(
    text: str,
    src_lang: str,
    tgt_lang: str,
    tok,
    mdl,
) -> str:
    """
    Shared IndicTrans2 pipeline:
    preprocess -> tokenize -> generate -> decode -> postprocess.
    """

    sentences = [text.strip()]

    batch = processor.preprocess_batch(
        sentences,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
    )

    print("Preprocessed batch:")
    print(batch)

    if batch is None:
        raise RuntimeError(
            "IndicTrans2 preprocessing returned None"
        )

    inputs = tok(
        batch,
        padding="longest",
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )

    if inputs is None:
        raise RuntimeError(
            "Tokenizer returned None"
        )

    print(
        "Tokenizer input keys:",
        list(inputs.keys()),
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        generated_tokens = mdl.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            num_beams=5,
            num_return_sequences=1,
            max_length=256,
            use_cache=False,
        )

    if generated_tokens is None:
        raise RuntimeError(
            "IndicTrans2 model returned None"
        )

    decoded = tok.batch_decode(
        generated_tokens,
        skip_special_tokens=True,
    )

    print("Decoded output:")
    print(decoded)

    output = processor.postprocess_batch(
        decoded,
        lang=tgt_lang,
    )

    print("Postprocessed output:")
    print(output)

    if not output:
        raise RuntimeError(
            "IndicTrans2 produced empty translation"
        )

    return output[0]


# ============================================================
# Indic -> English (existing behavior)
# ============================================================

def translate_text(
    text: str,
    source_language: str,
) -> str:

    if not text or not text.strip():
        return ""

    # English does not need translation
    if source_language.lower() == "english":
        return text

    if source_language not in LANGUAGE_CODES:
        raise ValueError(
            f"Unsupported source language: {source_language}"
        )

    return _run_translation(
        text,
        src_lang=LANGUAGE_CODES[source_language],
        tgt_lang=ENGLISH_CODE,
        tok=tokenizer,
        mdl=model,
    )


# ============================================================
# English -> Indic (new)
# ============================================================

def translate_from_english(
    text: str,
    target_language: str,
) -> str:

    if not text or not text.strip():
        return ""

    if target_language not in LANGUAGE_CODES:
        raise ValueError(
            f"Unsupported target language: {target_language}"
        )

    return _run_translation(
        text,
        src_lang=ENGLISH_CODE,
        tgt_lang=LANGUAGE_CODES[target_language],
        tok=reverse_tokenizer,
        mdl=reverse_model,
    )


# ============================================================
# HTTP Server
# ============================================================

class TranslatorHandler(BaseHTTPRequestHandler):

    # --------------------------------------------------------
    # JSON response helper
    # --------------------------------------------------------

    def _send_json(
        self,
        status_code: int,
        data: dict,
    ):

        response = json.dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(response)),
        )

        self.end_headers()

        self.wfile.write(response)

    # --------------------------------------------------------
    # Health endpoint
    # --------------------------------------------------------

    def do_GET(self):

        if self.path == "/health":

            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "indictrans2",
                    "model": MODEL_NAME,
                    "reverse_model": REVERSE_MODEL_NAME,
                    "directions": [
                        "indic_to_en",
                        "en_to_indic",
                    ],
                },
            )

            return

        self._send_json(
            404,
            {
                "error": "Not found",
            },
        )

    # --------------------------------------------------------
    # Translation endpoint
    # --------------------------------------------------------

    def do_POST(self):

        if self.path != "/translate":

            self._send_json(
                404,
                {
                    "error": "Not found",
                },
            )

            return

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0,
                )
            )

            body = self.rfile.read(
                content_length
            )

            payload = json.loads(
                body.decode("utf-8")
            )

            text = (payload.get("text") or "").strip()

            source_language = (
                payload.get("source_language") or ""
            ).strip()

            target_language = (
                payload.get("target_language") or ""
            ).strip()

            # ------------------------------------------------
            # Validate request
            # ------------------------------------------------

            if not text:

                self._send_json(
                    400,
                    {
                        "error": "text is required",
                    },
                )

                return

            if not source_language:

                self._send_json(
                    400,
                    {
                        "error": "source_language is required",
                    },
                )

                return

            # ------------------------------------------------
            # English -> Indic
            # ------------------------------------------------

            is_reverse = (
                source_language.lower() == "english"
                and target_language
                and target_language.lower() != "english"
            )

            if is_reverse:

                translated_text = translate_from_english(
                    text,
                    target_language,
                )

                self._send_json(
                    200,
                    {
                        "translated_text": translated_text,
                        "source_language": "English",
                        "target_language": target_language,
                    },
                )

                return

            # ------------------------------------------------
            # Indic -> English (existing behavior)
            # ------------------------------------------------

            translated_text = translate_text(
                text,
                source_language,
            )

            self._send_json(
                200,
                {
                    "translated_text": translated_text,
                    "source_language": source_language,
                    "target_language": "English",
                },
            )

        except Exception as exc:

            print("\n" + "=" * 70)
            print("TRANSLATION ERROR")
            print("=" * 70)

            traceback.print_exc()

            print("=" * 70 + "\n")

            self._send_json(
                500,
                {
                    "error": str(exc),
                    "type": type(exc).__name__,
                },
            )

    # --------------------------------------------------------
    # Cleaner console logging
    # --------------------------------------------------------

    def log_message(
        self,
        format,
        *args,
    ):

        print(
            f"[Translator] {format % args}"
        )


# ============================================================
# Start Server
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("INDICTRANS2 TRANSLATOR SERVICE")
    print("=" * 70)
    print(f"Host:          {HOST}")
    print(f"Port:          {PORT}")
    print(f"Indic -> En:   {MODEL_NAME}")
    print(f"En -> Indic:   {REVERSE_MODEL_NAME}")
    print("=" * 70)
    print()

    server = HTTPServer(
        (HOST, PORT),
        TranslatorHandler,
    )

    print(
        f"Translator service running on "
        f"http://{HOST}:{PORT}"
    )

    print("Available endpoints:")
    print(f"  GET  http://{HOST}:{PORT}/health")
    print(f"  POST http://{HOST}:{PORT}/translate")
    print()

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print(
            "\nStopping translator service..."
        )

        server.server_close()