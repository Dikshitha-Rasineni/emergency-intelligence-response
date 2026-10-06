from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from IndicTransToolkit import IndicProcessor
import torch

MODEL = "ai4bharat/indictrans2-indic-en-dist-200M"

TESTS = {
    "Tamil": (
        "tam_Taml",
        "பேருந்து நிலையம் அருகே ஒரு பெரிய விபத்து ஏற்பட்டுள்ளது. சேதமடைந்த பேருந்துக்குள் சுமார் 15 பேர் சிக்கியுள்ளனர், மேலும் ஒரு குழந்தைக்கு கடுமையான காயம் ஏற்பட்டுள்ளது. வாகனத்திலிருந்து எரிபொருள் கசிந்து கொண்டிருக்கிறது."
    ),
    "Telugu": (
        "tel_Telu",
        "బస్ స్టాండ్ సమీపంలో భారీ ప్రమాదం జరిగింది. దెబ్బతిన్న బస్సులో సుమారు 15 మంది చిక్కుకున్నారు, ఒక చిన్నారికి తీవ్ర గాయాలయ్యాయి. వాహనం నుంచి ఇంధనం లీక్ అవుతోంది."
    ),
    "Kannada": (
        "kan_Knda",
        "ಬಸ್ ನಿಲ್ದಾಣದ ಬಳಿ ದೊಡ್ಡ ಅಪಘಾತ ಸಂಭವಿಸಿದೆ. ಹಾನಿಗೊಳಗಾದ ಬಸ್ಸಿನೊಳಗೆ ಸುಮಾರು 15 ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ ಮತ್ತು ಒಂದು ಮಗುವಿಗೆ ಗಂಭೀರ ಗಾಯಗಳಾಗಿವೆ. ವಾಹನದಿಂದ ಇಂಧನ ಸೋರಿಕೆಯಾಗುತ್ತಿದೆ."
    ),
    "Malayalam": (
        "mal_Mlym",
        "ബസ് സ്റ്റാൻഡിന് സമീപം വലിയൊരു അപകടം സംഭവിച്ചു. തകർന്ന ബസിനുള്ളിൽ ഏകദേശം 15 പേർ കുടുങ്ങിക്കിടക്കുകയാണ്, ഒരു കുട്ടിക്ക് ഗുരുതരമായി പരിക്കേറ്റിട്ടുണ്ട്. വാഹനത്തിൽ നിന്ന് ഇന്ധനം ചോർന്നുകൊണ്ടിരിക്കുകയാണ്."
    ),
    "Hindi": (
        "hin_Deva",
        "बस स्टैंड के पास एक बड़ा हादसा हुआ है। क्षतिग्रस्त बस के अंदर लगभग 15 लोग फंसे हुए हैं और एक बच्चे को गंभीर चोट लगी है। वाहन से ईंधन लीक हो रहा है।"
    ),
}

tokenizer = AutoTokenizer.from_pretrained(
    MODEL,
    trust_remote_code=True
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL,
    trust_remote_code=True
)

processor = IndicProcessor(inference=True)

for language, (src_lang, text) in TESTS.items():

    print("\n" + "=" * 70)
    print(language)
    print("=" * 70)

    batch = processor.preprocess_batch(
        [text],
        src_lang=src_lang,
        tgt_lang="eng_Latn"
    )

    inputs = tokenizer(
        batch,
        padding="longest",
        truncation=True,
        return_tensors="pt"
    )

    with torch.no_grad():
        generated_tokens = model.generate(
            **inputs,
            max_length=256,
            num_beams=5,
            use_cache=False
        )

    decoded = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True
    )

    translated = processor.postprocess_batch(
        decoded,
        lang="eng_Latn"
    )

    print("INPUT:")
    print(text)

    print("\nENGLISH:")
    print(translated[0])

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
