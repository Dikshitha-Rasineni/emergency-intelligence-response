"""Canonical emergency categories, labels, and the citizen safety-guidance library.

GUIDANCE REVIEW STATUS: the English text is conservative general public-safety
advice written for this project. The Telugu, Tamil and Hindi versions are draft
translations that have NOT been reviewed by native-speaking emergency
professionals. Approved knowledge documents (RAG) are cited in addition when
available. Medical guidance deliberately contains no clinical instructions.
"""
from typing import Dict, List, Optional

CATEGORIES = (
    "road_accident", "fire", "gas_leak", "flood", "medical",
    "structural_collapse", "rescue", "security", "sos", "other",
)

CATEGORY_LABELS_EN = {
    "road_accident": "Road accident",
    "fire": "Fire",
    "gas_leak": "Smoke or gas leak",
    "flood": "Flood",
    "medical": "Medical emergency",
    "structural_collapse": "Structural collapse",
    "rescue": "Rescue required",
    "security": "Security threat",
    "sos": "SOS",
    "other": "Other emergency",
}

# Old free-text types stored by earlier versions -> canonical category
LEGACY_TYPE_MAP = {
    "major road accident": "road_accident",
    "commercial building fire": "fire",
    "urban flash flood & vehicle stall": "flood",
    "cardiac / acute medical crisis": "medical",
    "general emergency": "other",
}


def normalize_category(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.strip().lower().replace("-", "_").replace(" ", "_")
    if v in CATEGORIES:
        return v
    raw = value.strip().lower()
    if raw in LEGACY_TYPE_MAP:
        return LEGACY_TYPE_MAP[raw]
    for key, words in (
        ("road_accident", ("accident", "crash", "collision")),
        ("gas_leak", ("gas", "leak", "smoke")),
        ("fire", ("fire", "blaze", "flame")),
        ("flood", ("flood", "water")),
        ("medical", ("medical", "cardiac", "heart", "unconscious", "breath")),
        ("structural_collapse", ("collapse",)),
        ("rescue", ("rescue", "trapped")),
        ("security", ("security", "assault", "threat", "violence")),
        ("sos", ("sos",)),
    ):
        if any(w in raw for w in words):
            return key
    return "other"


def label(category: Optional[str]) -> str:
    return CATEGORY_LABELS_EN.get(category or "other", "Other emergency")


_COMMON_EN = "Call 112 (India emergency number) if you have not already."
_GUIDANCE: Dict[str, Dict[str, List[str]]] = {
    "road_accident": {
        "en": [
            "Move yourself to a safe place away from moving traffic if you can.",
            "Switch on hazard lights and warn approaching vehicles if it is safe to do so.",
            "Do not move a seriously injured person unless they are in immediate danger (fire, traffic).",
            "Keep the road clear for arriving ambulances and police.",
        ],
        "te": [
            "వీలైతే, కదులుతున్న వాహనాలకు దూరంగా సురక్షిత ప్రదేశానికి వెళ్ళండి.",
            "సురక్షితమైతే హజార్డ్ లైట్లు వేసి, వస్తున్న వాహనాలను హెచ్చరించండి.",
            "తక్షణ ప్రమాదం (మంటలు, ట్రాఫిక్) లేకపోతే తీవ్రంగా గాయపడిన వ్యక్తిని కదిలించవద్దు.",
            "అంబులెన్స్ మరియు పోలీసుల కోసం రహదారిని ఖాళీగా ఉంచండి.",
        ],
        "ta": [
            "முடிந்தால், ஓடும் வாகனங்களிலிருந்து விலகி பாதுகாப்பான இடத்திற்குச் செல்லுங்கள்.",
            "பாதுகாப்பாக இருந்தால் அபாய விளக்குகளை இயக்கி, வரும் வாகனங்களை எச்சரியுங்கள்.",
            "உடனடி ஆபத்து (தீ, போக்குவரத்து) இல்லாவிட்டால் கடுமையாக காயமடைந்தவரை நகர்த்த வேண்டாம்.",
            "ஆம்புலன்ஸ் மற்றும் காவல்துறைக்கு சாலையைத் தெளிவாக வைத்திருங்கள்.",
        ],
        "hi": [
            "हो सके तो चलते वाहनों से दूर किसी सुरक्षित जगह पर चले जाएँ।",
            "सुरक्षित हो तो हैज़र्ड लाइट चालू करें और आने वाले वाहनों को सावधान करें।",
            "तत्काल खतरा (आग, ट्रैफ़िक) न हो तो गंभीर रूप से घायल व्यक्ति को न हिलाएँ।",
            "एम्बुलेंस और पुलिस के लिए सड़क खाली रखें।",
        ],
    },
    "fire": {
        "en": [
            "Leave the area immediately and do not go back inside a burning building.",
            "Stay low if there is smoke; cover your nose and mouth with cloth.",
            "Use stairs, not lifts.",
            "Close doors behind you if it does not slow your escape.",
        ],
        "te": [
            "వెంటనే ఆ ప్రాంతం నుండి బయటకు వెళ్ళండి; మంటలు ఉన్న భవనంలోకి తిరిగి వెళ్ళవద్దు.",
            "పొగ ఉంటే వంగి నడవండి; ముక్కు, నోటిని గుడ్డతో కప్పుకోండి.",
            "లిఫ్టులు కాకుండా మెట్లను ఉపయోగించండి.",
            "బయటకు రావడం ఆలస్యం కాకపోతే, వెనుక ఉన్న తలుపులు మూసివేయండి.",
        ],
        "ta": [
            "உடனே அந்த இடத்தை விட்டு வெளியேறுங்கள்; எரியும் கட்டிடத்திற்குள் மீண்டும் செல்ல வேண்டாம்.",
            "புகை இருந்தால் குனிந்து செல்லுங்கள்; மூக்கு, வாயை துணியால் மூடுங்கள்.",
            "மின்தூக்கியை அல்ல, படிக்கட்டுகளைப் பயன்படுத்துங்கள்.",
            "வெளியேறுவது தாமதமாகாவிட்டால் பின்னால் உள்ள கதவுகளை மூடுங்கள்.",
        ],
        "hi": [
            "तुरंत उस जगह से निकल जाएँ और जलती इमारत में वापस न जाएँ।",
            "धुआँ हो तो झुककर चलें; नाक और मुँह को कपड़े से ढकें।",
            "लिफ़्ट नहीं, सीढ़ियों का इस्तेमाल करें।",
            "अगर निकलने में देर न हो तो पीछे के दरवाज़े बंद कर दें।",
        ],
    },
    "gas_leak": {
        "en": [
            "Leave the area and move to fresh air.",
            "Do not switch electrical items on or off and do not use flames or lighters.",
            "If it is safe, open windows and doors on your way out.",
            "Report from a safe distance, away from the smell of gas.",
        ],
        "te": [
            "ఆ ప్రాంతం నుండి బయటకు వెళ్ళి తాజా గాలిలోకి చేరండి.",
            "విద్యుత్ స్విచ్‌లను ఆన్ లేదా ఆఫ్ చేయవద్దు; మంట లేదా లైటర్ ఉపయోగించవద్దు.",
            "సురక్షితమైతే, బయటకు వెళ్ళేటప్పుడు కిటికీలు, తలుపులు తెరవండి.",
            "గ్యాస్ వాసనకు దూరంగా, సురక్షిత దూరం నుండి సమాచారం ఇవ్వండి.",
        ],
        "ta": [
            "அந்த இடத்தை விட்டு வெளியேறி சுத்தமான காற்றுக்குச் செல்லுங்கள்.",
            "மின் சுவிட்சுகளை இயக்கவோ அணைக்கவோ வேண்டாம்; தீ அல்லது லைட்டர் பயன்படுத்த வேண்டாம்.",
            "பாதுகாப்பாக இருந்தால், வெளியேறும்போது ஜன்னல்களையும் கதவுகளையும் திறங்கள்.",
            "எரிவாயு வாசனையிலிருந்து விலகி, பாதுகாப்பான தூரத்திலிருந்து தகவல் தெரிவியுங்கள்.",
        ],
        "hi": [
            "उस जगह से निकलकर खुली हवा में जाएँ।",
            "बिजली के स्विच चालू या बंद न करें; आग या लाइटर का इस्तेमाल न करें।",
            "सुरक्षित हो तो निकलते समय खिड़कियाँ और दरवाज़े खोल दें।",
            "गैस की गंध से दूर, सुरक्षित दूरी से सूचना दें।",
        ],
    },
    "flood": {
        "en": [
            "Do not walk, swim or drive through moving floodwater.",
            "Move to higher ground if it is safe to get there.",
            "Stay away from electric poles, fallen wires and open drains.",
            "Follow official evacuation instructions from local authorities.",
        ],
        "te": [
            "ప్రవహించే వరద నీటిలో నడవవద్దు, ఈదవద్దు లేదా వాహనం నడపవద్దు.",
            "సురక్షితంగా చేరగలిగితే ఎత్తైన ప్రదేశానికి వెళ్ళండి.",
            "విద్యుత్ స్తంభాలు, తెగిన తీగలు, తెరిచి ఉన్న కాలువలకు దూరంగా ఉండండి.",
            "స్థానిక అధికారుల అధికారిక తరలింపు సూచనలను పాటించండి.",
        ],
        "ta": [
            "ஓடும் வெள்ள நீரில் நடக்கவோ, நீந்தவோ, வாகனம் ஓட்டவோ வேண்டாம்.",
            "பாதுகாப்பாகச் செல்ல முடிந்தால் உயரமான இடத்திற்குச் செல்லுங்கள்.",
            "மின் கம்பங்கள், அறுந்த கம்பிகள், திறந்த வடிகால்களிலிருந்து விலகி இருங்கள்.",
            "உள்ளூர் அதிகாரிகளின் அதிகாரப்பூர்வ வெளியேற்ற அறிவுறுத்தல்களைப் பின்பற்றுங்கள்.",
        ],
        "hi": [
            "बहते बाढ़ के पानी में न चलें, न तैरें और न गाड़ी चलाएँ।",
            "सुरक्षित रूप से पहुँच सकें तो ऊँची जगह पर चले जाएँ।",
            "बिजली के खंभों, टूटे तारों और खुले नालों से दूर रहें।",
            "स्थानीय अधिकारियों के आधिकारिक निकासी निर्देशों का पालन करें।",
        ],
    },
    "medical": {
        "en": [
            "Stay with the person and keep the area around them clear.",
            "If you are trained in first aid, follow your training; otherwise follow the emergency operator's instructions.",
            "Do not give food, drink or medicine unless a medical professional tells you to.",
            "Keep the entrance open and send someone to guide the ambulance in.",
        ],
        "te": [
            "ఆ వ్యక్తి దగ్గరే ఉండండి, చుట్టూ ఉన్న ప్రదేశాన్ని ఖాళీగా ఉంచండి.",
            "మీకు ప్రథమ చికిత్స శిక్షణ ఉంటే దాన్ని పాటించండి; లేకపోతే అత్యవసర ఆపరేటర్ సూచనలను పాటించండి.",
            "వైద్య నిపుణులు చెప్పకపోతే ఆహారం, నీరు లేదా మందులు ఇవ్వవద్దు.",
            "ప్రవేశ ద్వారం తెరిచి ఉంచి, అంబులెన్స్‌కు దారి చూపడానికి ఎవరినైనా పంపండి.",
        ],
        "ta": [
            "அந்த நபருடன் இருங்கள்; அவரைச் சுற்றியுள்ள இடத்தைத் தெளிவாக வைத்திருங்கள்.",
            "முதலுதவி பயிற்சி இருந்தால் அதைப் பின்பற்றுங்கள்; இல்லையெனில் அவசர உதவி இயக்குநரின் அறிவுறுத்தல்களைப் பின்பற்றுங்கள்.",
            "மருத்துவர் சொல்லாவிட்டால் உணவு, நீர் அல்லது மருந்து கொடுக்க வேண்டாம்.",
            "நுழைவாயிலைத் திறந்து வைத்து, ஆம்புலன்ஸுக்கு வழிகாட்ட ஒருவரை அனுப்புங்கள்.",
        ],
        "hi": [
            "व्यक्ति के पास रहें और आसपास की जगह खाली रखें।",
            "अगर आपको प्राथमिक चिकित्सा का प्रशिक्षण है तो उसका पालन करें; नहीं तो आपातकालीन ऑपरेटर के निर्देश मानें।",
            "जब तक कोई चिकित्सा पेशेवर न कहे, खाना, पानी या दवा न दें।",
            "प्रवेश द्वार खुला रखें और एम्बुलेंस को रास्ता दिखाने के लिए किसी को भेजें।",
        ],
    },
    "structural_collapse": {
        "en": [
            "Move away from the damaged structure; more parts may fall.",
            "Do not re-enter to search for people; tell rescuers where people were last seen.",
            "Avoid using flames; there may be gas leaks.",
        ],
        "te": [
            "దెబ్బతిన్న కట్టడం నుండి దూరంగా వెళ్ళండి; మరిన్ని భాగాలు పడిపోవచ్చు.",
            "వ్యక్తులను వెతకడానికి లోపలికి వెళ్ళవద్దు; వారు చివరిగా ఎక్కడ కనిపించారో రక్షణ బృందానికి చెప్పండి.",
            "గ్యాస్ లీక్ ఉండవచ్చు కాబట్టి మంటను ఉపయోగించవద్దు.",
        ],
        "ta": [
            "சேதமடைந்த கட்டமைப்பிலிருந்து விலகிச் செல்லுங்கள்; மேலும் பகுதிகள் விழலாம்.",
            "ஆட்களைத் தேட உள்ளே மீண்டும் செல்ல வேண்டாம்; அவர்கள் கடைசியாக எங்கு இருந்தனர் என்பதை மீட்புக் குழுவிடம் கூறுங்கள்.",
            "எரிவாயு கசிவு இருக்கலாம் என்பதால் தீயைப் பயன்படுத்த வேண்டாம்.",
        ],
        "hi": [
            "क्षतिग्रस्त ढाँचे से दूर हट जाएँ; और हिस्से गिर सकते हैं।",
            "लोगों को ढूँढने के लिए अंदर वापस न जाएँ; बचावकर्मियों को बताएँ कि लोग आखिरी बार कहाँ देखे गए थे।",
            "गैस रिसाव हो सकता है, इसलिए आग का इस्तेमाल न करें।",
        ],
    },
    "other": {
        "en": [
            "Move away from any immediate danger.",
            "Stay where responders can find you and keep your phone switched on.",
            "Follow instructions from police, fire or medical responders when they arrive.",
        ],
        "te": [
            "ఏదైనా తక్షణ ప్రమాదం నుండి దూరంగా వెళ్ళండి.",
            "సహాయక బృందాలు మిమ్మల్ని కనుగొనగలిగే చోట ఉండండి; మీ ఫోన్‌ను ఆన్‌లో ఉంచండి.",
            "పోలీసులు, అగ్నిమాపక లేదా వైద్య సిబ్బంది వచ్చినప్పుడు వారి సూచనలను పాటించండి.",
        ],
        "ta": [
            "உடனடி ஆபத்திலிருந்து விலகிச் செல்லுங்கள்.",
            "மீட்புக் குழுவினர் உங்களைக் கண்டுபிடிக்கக்கூடிய இடத்தில் இருங்கள்; உங்கள் தொலைபேசியை இயக்கத்தில் வைத்திருங்கள்.",
            "காவல், தீயணைப்பு அல்லது மருத்துவக் குழுவினர் வந்ததும் அவர்களின் அறிவுறுத்தல்களைப் பின்பற்றுங்கள்.",
        ],
        "hi": [
            "किसी भी तत्काल खतरे से दूर हट जाएँ।",
            "ऐसी जगह रहें जहाँ बचावकर्मी आपको ढूँढ सकें और अपना फ़ोन चालू रखें।",
            "पुलिस, दमकल या चिकित्सा कर्मियों के आने पर उनके निर्देशों का पालन करें।",
        ],
    },
}
_GUIDANCE["rescue"] = _GUIDANCE["structural_collapse"]
_GUIDANCE["security"] = {
    "en": ["Move to a safe place away from the threat if you can.",
           "Do not confront anyone; wait for police.",
           "Keep your phone on and silent if you are hiding."],
    "te": ["వీలైతే ప్రమాదం నుండి దూరంగా సురక్షిత ప్రదేశానికి వెళ్ళండి.",
           "ఎవరినీ ఎదుర్కోవద్దు; పోలీసుల కోసం వేచి ఉండండి.",
           "మీరు దాక్కుని ఉంటే ఫోన్‌ను ఆన్‌లో, సైలెంట్‌లో ఉంచండి."],
    "ta": ["முடிந்தால் அச்சுறுத்தலிலிருந்து விலகி பாதுகாப்பான இடத்திற்குச் செல்லுங்கள்.",
           "யாரையும் எதிர்கொள்ள வேண்டாம்; காவல்துறைக்காகக் காத்திருங்கள்.",
           "நீங்கள் மறைந்திருந்தால் தொலைபேசியை இயக்கத்திலும் அமைதி நிலையிலும் வைத்திருங்கள்."],
    "hi": ["हो सके तो खतरे से दूर किसी सुरक्षित जगह पर जाएँ।",
           "किसी का सामना न करें; पुलिस का इंतज़ार करें।",
           "अगर आप छिपे हैं तो फ़ोन चालू और साइलेंट रखें।"],
}
_GUIDANCE["sos"] = _GUIDANCE["other"]

_CALL_112 = {
    "en": _COMMON_EN,
    "te": "ఇంకా కాల్ చేయకపోతే 112 (భారత అత్యవసర నంబర్)కు కాల్ చేయండి.",
    "ta": "இன்னும் அழைக்கவில்லை என்றால் 112 (இந்திய அவசர எண்) ஐ அழையுங்கள்.",
    "hi": "अगर अभी तक कॉल नहीं किया है तो 112 (भारत आपातकालीन नंबर) पर कॉल करें।",
}

GUIDANCE_SOURCE = {
    "title": "RESQ.AI baseline public-safety guidance",
    "publisher": "RESQ.AI project (draft)",
    "review_status": "unreviewed_draft",
    "note": "General advice only. Not medical advice. Telugu/Tamil/Hindi translations pending native-speaker review.",
}


def guidance_for(category: Optional[str], lang: str) -> Dict[str, object]:
    cat = category if category in _GUIDANCE else "other"
    lib = _GUIDANCE[cat]
    used_lang = lang if lang in lib else "en"
    items = [_CALL_112.get(used_lang, _COMMON_EN)] + list(lib[used_lang])
    return {
        "category": cat,
        "language": used_lang,
        "language_fallback": used_lang != lang,
        "items": items,
        "source": GUIDANCE_SOURCE,
    }


SUPPORTED_UI_LANGUAGES = ("en", "te", "ta", "hi")
