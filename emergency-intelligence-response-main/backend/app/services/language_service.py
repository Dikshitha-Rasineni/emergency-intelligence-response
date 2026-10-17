"""
Multilingual Processing Engine for RESQ.AI.

Supports Telugu, Tamil, Hindi, Kannada, Malayalam, and English:
  - Script-based deterministic language detection (zero-dependency, <0.01ms)
  - Multilingual keyword and entity extraction (emergencies, casualties, critical hazards)
  - Localized non-diagnostic public safety precautions
  - Localized operational directives for Hospital, Police, Fire, and CAD
  - Localized severity and priority display labels
"""

import re
from typing import Dict, List, Tuple, Optional


class LanguageService:
    LANGUAGE_NAMES = {
        "en": "English",
        "te": "Telugu (తెలుగు)",
        "ta": "Tamil (தமிழ்)",
        "hi": "Hindi (हिन्दी)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ml": "Malayalam (മലയാളം)",
    }

    SEVERITY_LABELS = {
        "en": {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MODERATE": "MODERATE", "LOW": "LOW"},
        "te": {"CRITICAL": "అత్యవసరం (CRITICAL)", "HIGH": "అధికం (HIGH)", "MODERATE": "మధ్యస్థం (MODERATE)", "LOW": "సాధారణం (LOW)"},
        "ta": {"CRITICAL": "அதிமுக்கியம் (CRITICAL)", "HIGH": "உயர் (HIGH)", "MODERATE": "நடுத்தரம் (MODERATE)", "LOW": "குறைவு (LOW)"},
        "hi": {"CRITICAL": "गंभीर (CRITICAL)", "HIGH": "उच्च (HIGH)", "MODERATE": "मध्यम (MODERATE)", "LOW": "सामान्य (LOW)"},
        "kn": {"CRITICAL": "ಗಂಭೀರ (CRITICAL)", "HIGH": "ಉನ್ನತ (HIGH)", "MODERATE": "ಮಧ್ಯಮ (MODERATE)", "LOW": "ಸಾಮಾನ್ಯ (LOW)"},
        "ml": {"CRITICAL": "അത്യാഹിതം (CRITICAL)", "HIGH": "ഉയർന്നത് (HIGH)", "MODERATE": "മിതമായത് (MODERATE)", "LOW": "കുറഞ്ഞത് (LOW)"},
    }

    # Number words in Indian languages
    NUMBER_WORDS = {
        "en": {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10},
        "te": {"ఒకటి": 1, "ఒకరు": 1, "రెండు": 2, "ఇద్దరు": 2, "మూడు": 3, "ముగ్గురు": 3, "నలుగురు": 4, "నాలుగు": 4, "ఐదుగురు": 5, "ఐదు": 5, "పది": 10},
        "ta": {"ஒன்று": 1, "ஒருவர்": 1, "இரண்டு": 2, "இருவர்": 2, "மூன்று": 3, "மூவர்": 3, "நான்கு": 4, "நால்வர்": 4, "ஐந்து": 5, "ஐவர்": 5, "பத்து": 10},
        "hi": {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10},
        "kn": {"ಒಂದು": 1, "ಒಬ್ಬರು": 1, "ಎರಡು": 2, "ಇಬ್ಬರು": 2, "ಮೂರು": 3, "ಮೂವರು": 3, "ನಾಲ್ಕು": 4, "ನಾಲ್ವರು": 4, "ಐದು": 5, "ಐವರು": 5, "ಹತ್ತು": 10},
        "ml": {"ഒന്ന്": 1, "ഒരാൾ": 1, "രണ്ട്": 2, "ഇരുവർ": 2, "മൂന്ന്": 3, "മൂന്നുപേർ": 3, "നാല്": 4, "നാലുപേർ": 4, "അഞ്ച്": 5, "അഞ്ചുപേർ": 5, "പത്ത്": 10},
    }

    # Emergency type keywords by language
    TYPE_KEYWORDS = {
        "Major Road Accident": {
            "en": ["accident", "crash", "collision", "overturned", "fender bender", "highway"],
            "te": ["ప్రమాదం", "రోడ్డు ప్రమాదం", "యాక్సిడెంట్", "ఢీకొంది", "బోల్తా"],
            "ta": ["விபத்து", "சாலை விபத்து", "மோதியது", "கவிழ்ந்தது"],
            "hi": ["दुर्घटना", "सड़क दुर्घटना", "एक्सीडेंट", "टक्कर", "पलट गई"],
            "kn": ["ಅಪಘಾತ", "ರಸ್ತೆ ಅಪಘಾತ", "ಡಿಕ್ಕಿ", "ಉರುಳಿಬಿದ್ದಿದೆ"],
            "ml": ["അപകടം", "റോഡപകടം", "കൂട്ടിയിടി", "മറിഞ്ഞു"],
        },
        "Commercial Building Fire": {
            "en": ["fire", "smoke", "blaze", "burning", "explosion", "flames"],
            "te": ["మంటలు", "అగ్ని", "కాలిపోతోంది", "పొగ", "పేలుడు", "నిప్పు"],
            "ta": ["தீ", "நெருப்பு", "தீ விபத்து", "புகை", "வெடிப்பு", "எரிகிறது"],
            "hi": ["आग", "धुआं", "आग लग गई", "ब्लेज", "विस्फोट", "जल रहा"],
            "kn": ["ಬೆಂಕಿ", "ಹೊಗೆ", "ಜ್ವಾಲೆ", "ಸ್ಪೋಟ", "ಸುಡುತ್ತಿದೆ"],
            "ml": ["തീ", "തീപിടുത്തം", "പുക", "സ്ഫോടനം", "കത്തുന്നു"],
        },
        "Urban Flash Flood & Vehicle Stall": {
            "en": ["flood", "waterlogging", "submerged", "drowning", "rising water", "water"],
            "te": ["వరద", "నీరు", "మునిగిపోయింది", "నీటిమట్టం", "ముంపు"],
            "ta": ["வெள்ளம்", "நீர்", "மூழ்கியது", "வெள்ளப்பெருக்கு"],
            "hi": ["बाढ़", "जलभराव", "डूब", "पानी भर गया", "तेज बहाव"],
            "kn": ["ಪ್ರವಾಹ", "ನೀರು", "ಮುಳುಗಿದೆ", "ನೀರು ತುಂಬಿದೆ"],
            "ml": ["വെള്ളപ്പൊക്കം", "വെള്ളം", "മുങ്ങി", "വെള്ളം കയറി"],
        },
        "Cardiac / Acute Medical Crisis": {
            "en": ["cardiac", "heart attack", "collapsed", "unresponsive", "cpr", "stroke"],
            "te": ["గుండెపోటు", "స్పృహతప్పారు", "కుప్పకూలిపోయారు", "శ్వాస ఆడట్లేదు"],
            "ta": ["மாரடைப்பு", "மயக்கம்", "சுயநினைவு இழந்தார்", "மூச்சுத்திணறல்"],
            "hi": ["दिल का दौरा", "हार्ट अटैक", "बेहोश", "गिर पड़ा", "सांस नहीं ले पा रहा"],
            "kn": ["ಹೃದಯಾಘಾತ", "ಪ್ರಜ್ಞಾಹೀನ", "ಕುಸಿದುಬಿದ್ದಿದ್ದಾರೆ", "ಉಸಿರಾಟ ತೊಂದರೆ"],
            "ml": ["ഹൃദയാഘാതം", "കുഴഞ്ഞുവീണു", "അബോധാവസ്ഥ", "ശ്വാസമെടുക്കാൻ ബുദ്ധിമുട്ട്"],
        },
    }

    # Critical indicators keywords by language
    INDICATOR_KEYWORDS = {
        "Unconscious casualty reported": {
            "en": ["unconscious", "unresponsive", "knocked out"],
            "te": ["స్పృహ కోల్పోయారు", "స్పృహ లేదు", "స్పృహతప్పారు"],
            "ta": ["மயக்கம்", "சுயநினைவு இல்லை", "மயக்கமடைந்தார்"],
            "hi": ["बेहोश", "अचेत", "होश नहीं है"],
            "kn": ["ಪ್ರಜ್ಞಾಹೀನ", "ಪ್ರಜ್ಞೆ ತಪ್ಪಿದೆ", "ಎಚ್ಚರವಿಲ್ಲ"],
            "ml": ["അബോധാവസ്ഥയിൽ", "ബോധമില്ല", "ബോധംകെട്ടു"],
        },
        "Occupants trapped on scene": {
            "en": ["trapped", "pinned", "stuck inside", "cannot get out"],
            "te": ["చిక్కుకున్నారు", "ఇరుక్కుపోయారు", "బయటకు రాలేకపోతున్నారు"],
            "ta": ["சிக்கியுள்ளனர்", "வெளியே வர முடியவில்லை", "அகப்பட்டுள்ளனர்"],
            "hi": ["फंसे हुए", "अंदर फंसे", "बाहर नहीं निकल पा रहे"],
            "kn": ["ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ", "ಹೊರಬರಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ"],
            "ml": ["കുടുങ്ങി", "പുറത്തിറങ്ങാൻ പറ്റുന്നില്ല", "അകപ്പെട്ടു"],
        },
        "Hazardous smoke or gas cylinder condition": {
            "en": ["smoke", "gas", "cylinder", "chemical", "toxic"],
            "te": ["పొగ", "గ్యాస్", "సిలిండర్", "విషవాయువు"],
            "ta": ["புகை", "எரிவாயு", "சிலிண்டர்", "நச்சு"],
            "hi": ["धुआं", "गैस", "सिलेंडर", "जहरीला"],
            "kn": ["ಹೊಗೆ", "ಅನಿಲ", "ಸಿಲಿಂಡರ್", "ವಿಷಕಾರಿ"],
            "ml": ["പുക", "ഗ്യാസ്", "സിലിണ്ടർ", "വിഷവാതകം"],
        },
    }

    # Injury keywords
    INJURY_KEYWORDS = {
        "en": ["injured", "injuries", "hurt", "bleeding", "wounded", "casualties"],
        "te": ["గాయపడ్డారు", "గాయాలు", "రక్తం", "దెబ్బతిన్నారు"],
        "ta": ["காயமடைந்துள்ளனர்", "காயம்", "இரத்தம்", "பாதிக்கப்பட்டுள்ளனர்"],
        "hi": ["घायल", "चोट", "जख्मी", "खून"],
        "kn": ["ಗಾಯಗೊಂಡಿದ್ದಾರೆ", "ಗಾಯ", "ರಕ್ತಸ್ರಾವ"],
        "ml": ["പരിക്കേറ്റു", "മുറിവ്", "രക്തം"],
    }

    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Detects language from text using Unicode character distribution.
        Deterministic, fast (<0.01ms), robust against short inputs.
        """
        if not text or not text.strip():
            return "en"

        counts = {
            "te": len(re.findall(r"[\u0C00-\u0C7F]", text)),
            "ta": len(re.findall(r"[\u0B80-\u0BFF]", text)),
            "hi": len(re.findall(r"[\u0900-\u097F]", text)),
            "kn": len(re.findall(r"[\u0C80-\u0CFF]", text)),
            "ml": len(re.findall(r"[\u0D00-\u0D7F]", text)),
        }

        max_lang, max_count = max(counts.items(), key=lambda item: item[1])
        if max_count >= 2:
            return max_lang
        return "en"

    @classmethod
    def get_localized_severity(cls, severity: str, lang: str = "en") -> str:
        return cls.SEVERITY_LABELS.get(lang, cls.SEVERITY_LABELS["en"]).get(severity.upper(), severity)

    @classmethod
    def extract_numbers_and_injuries(cls, text: str, lang: str = "en") -> Tuple[int, int]:
        """Extracts (injuries, affected_people) using language-specific words and Arabic/Indic numerals."""
        lower = text.lower()
        num_dict = cls.NUMBER_WORDS.get(lang, cls.NUMBER_WORDS["en"])

        injuries = 0
        affected = 0

        # Check digits
        digit_matches = re.findall(r"\b(\d+)\b", text)
        digits = [int(d) for d in digit_matches if int(d) < 500]

        # Check word numbers
        found_nums = []
        for word, val in num_dict.items():
            if word in lower:
                found_nums.append(val)

        all_nums = digits + found_nums
        if all_nums:
            injuries = max(all_nums) if any(kw in lower for kw in cls.INJURY_KEYWORDS.get(lang, [])) else (all_nums[0] if len(all_nums) == 1 else 0)
            affected = max(all_nums) if all_nums else 0
        else:
            if any(kw in lower for kw in cls.INJURY_KEYWORDS.get(lang, [])):
                injuries = 1
                affected = 1

        return injuries, max(affected, injuries)

    @classmethod
    def extract_emergency_type(cls, text: str, lang: str = "en") -> str:
        """Determines emergency type across all languages."""
        lower = text.lower()
        for type_name, lang_dict in cls.TYPE_KEYWORDS.items():
            keywords = lang_dict.get(lang, []) + lang_dict.get("en", [])
            if any(kw in lower for kw in keywords):
                return type_name
        return "General Emergency"

    @classmethod
    def extract_critical_indicators(cls, text: str, lang: str = "en") -> List[str]:
        """Detects critical indicators in the specified language."""
        lower = text.lower()
        indicators = []
        for ind_name, lang_dict in cls.INDICATOR_KEYWORDS.items():
            keywords = lang_dict.get(lang, []) + lang_dict.get("en", [])
            if any(kw in lower for kw in keywords):
                indicators.append(ind_name)
        return indicators

    @classmethod
    def get_precautions(cls, emergency_type: str, lang: str = "en") -> List[str]:
        """Returns non-diagnostic public safety precautions in the requested language."""
        if lang == "te":
            if "fire" in emergency_type.lower() or "అగ్ని" in emergency_type:
                return [
                    "పొగ కింద నేలపై వంగి పాకండి — శుభ్రమైన గాలి నేల నుండి 1 అడుగు ఎత్తులో ఉంటుంది.",
                    "ఎటువంటి పరిస్థితుల్లోనూ లిఫ్టులను ఉపయోగించవద్దు; అత్యవసర మెట్లను మాత్రమే ఉపయోగించండి.",
                    "మంటలు వ్యాపించకుండా ఉండటానికి బయటకు వచ్చేటప్పుడు తలుపులు మూసివేయండి.",
                    "భవనానికి ఎదురుగా, గాలి వీచే దిశలో సురక్షిత ప్రదేశానికి చేరుకోండి.",
                    "బట్టలకు మంటలు అంటుకుంటే: వెంటనే ఆగండి, నేలపై పడుకోండి, దొర్లండి (Stop, Drop, Roll).",
                ]
            elif "flood" in emergency_type.lower() or "వరద" in emergency_type:
                return [
                    "ప్రవహించే వరద నీటిలో నడవడానికి లేదా వాహనాలు నడపడానికి ప్రయత్నించవద్దు.",
                    "నీటిలో మునిగిన విద్యుత్ వైర్లు మరియు తెరిచి ఉన్న మ్యాన్‌హోల్స్ పట్ల జాగ్రత్తగా ఉండండి.",
                    "రెస్క్యూ బృందాలు వచ్చే వరకు ఎత్తైన ప్రదేశంలో లేదా భవనం పైకప్పుపై వేచి ఉండండి.",
                    "సహాయం కోసం ప్రకాశవంతమైన వస్త్రం లేదా టార్చ్‌లైట్‌తో సంకేతాలు ఇవ్వండి.",
                ]
            elif "cardiac" in emergency_type.lower() or "గుండెపోటు" in emergency_type:
                return [
                    "పారామెడిక్స్ వచ్చే వరకు ఛాతీపై నిమిషానికి 100-120 సార్లు ఆగకుండా ఒత్తండి (CPR).",
                    "ఛాతీ మధ్యలో కనీసం 2 అంగుళాల లోతుగా గట్టిగా మరియు వేగంగా ఒత్తండి.",
                    "దగ్గరలోని ఆటోమేటెడ్ డీఫిబ్రిలేటర్ (AED) తీసుకురావడానికి ఇతరులను పంపండి.",
                    "అంబులెన్స్ సిబ్బంది సులభంగా లోపలికి రావడానికి తలుపులు తెరిచి ఉంచండి.",
                ]
            else:
                return [
                    "తీవ్రంగా గాయపడిన వ్యక్తులను మంటలు లేదా పేలుడు ప్రమాదం లేకపోతే కదల్చవద్దు.",
                    "రహదారి రద్దీకి దూరంగా, సురక్షితమైన ప్రదేశంలో నిలబడండి.",
                    "వాహన హజార్డ్ లైట్లు వేయండి మరియు ఇతర వాహనాలకు హెచ్చరిక ఇవ్వండి.",
                    "అత్యవసర అంబులెన్స్ రాక కోసం రహదారి మార్గాన్ని ఖాళీగా ఉంచండి.",
                ]

        elif lang == "ta":
            if "fire" in emergency_type.lower():
                return [
                    "புகைக்கு கீழே தவழ்ந்து செல்லுங்கள் — தரைக்கு அருகில் சுத்தமான காற்று இருக்கும்.",
                    "எந்த சூழ்நிலையிலும் மின்தூக்கியை (லிப்ட்) பயன்படுத்தாதீர்கள்; தீயணைப்பு படிக்கட்டுகளைப் பயன்படுத்துங்கள்.",
                    "வெளியேறும்போது தீ பரவாமல் தடுக்க கதவுகளை மூடிவிட்டு வாருங்கள்.",
                    "ஆடைகளில் தீ பிடித்தால்: உடனே நில்லுங்கள், கீழே விழுங்கள், உருளுங்கள் (Stop, Drop, Roll).",
                ]
            elif "flood" in emergency_type.lower():
                return [
                    "பாய்ந்தோடும் வெள்ள நீரில் நடக்கவோ அல்லது வாகனங்களை ஓட்டவோ முயற்சிக்காதீர்கள்.",
                    "நீரில் மூழ்கிய மின்சார கம்பிகள் மற்றும் திறந்த பாதாள சாக்கடைகளில் எச்சரிக்கையாக இருங்கள்.",
                    "மீட்புக் குழுக்கள் வரும் வரை உயரமான இடத்திலோ அல்லது மாடியிலோ பாதுகாப்பாக இருங்கள்.",
                ]
            elif "cardiac" in emergency_type.lower():
                return [
                    "ஆம்புலன்ஸ் வரும் வரை நிமிடத்திற்கு 100-120 முறை இடைவிடாமல் மார்பு அழுத்தங்களை (CPR) செய்யுங்கள்.",
                    "மார்பின் நடுவில் குறைந்தது 2 அங்குல ஆழத்திற்கு வேகமாகவும் பலமாகவும் அழுத்தவும்.",
                    "அருகிலுள்ள முதலுதவி கருவியை (AED) எடுத்துவர யாரையாவது உடனடியாக அனுப்புங்கள்.",
                ]
            else:
                return [
                    "காயமடைந்தவர்களை தீ அல்லது வெடிப்பு ஆபத்து இல்லாவிட்டால் அசைக்காதீர்கள்.",
                    "வாகன போக்குவரத்தில் இருந்து விலகி பாதுகாப்பான இடத்தில் நில்லுங்கள்.",
                    "அவசர ஆம்புலன்ஸ் எளிதாக வந்து சேர பாதையை காலியாக வையுங்கள்.",
                ]

        elif lang == "hi":
            if "fire" in emergency_type.lower():
                return [
                    "धुएं के नीचे झुककर रेंगें — फर्श से 1 फीट की ऊंचाई पर साफ हवा रहती है।",
                    "किसी भी स्थिति में लिफ्ट का प्रयोग न करें; आपातकालीन सीढ़ियों का उपयोग करें।",
                    "आग को फैलने से रोकने के लिए बाहर निकलते समय दरवाजे बंद कर दें।",
                    "यदि कपड़ों में आग लग जाए: तुरंत रुकें, जमीन पर लेटें और लुढ़कें (Stop, Drop, Roll)।",
                ]
            elif "flood" in emergency_type.lower():
                return [
                    "बहते हुए बाढ़ के पानी में पैदल चलने या गाड़ी चलाने की कोशिश बिल्कुल न करें।",
                    "डूबे हुए बिजली के तारों और खुले मैनहोल से अत्यधिक सावधान रहें।",
                    "राहत दल के आने तक किसी ऊंची और सुरक्षित छत पर रहें।",
                ]
            elif "cardiac" in emergency_type.lower():
                return [
                    "एम्बुलेंस आने तक सीने पर प्रति मिनट 100-120 बार निरंतर दबाव (CPR) दें।",
                    "सीने के बीच में कम से कम 2 इंच गहरा और तेजी से दबाव डालें।",
                    "आसपास किसी को तुरंत डिफाइब्रिलेटर (AED) लाने के लिए भेजें।",
                ]
            else:
                return [
                    "आग या विस्फोट का खतरा न होने तक गंभीर रूप से घायल व्यक्ति को न हिलाएं।",
                    "सड़क यातायात से दूर किसी सुरक्षित स्थान पर खड़े रहें।",
                    "आपातकालीन एम्बुलेंस के आवागमन के लिए रास्ता खुला रखें।",
                ]

        elif lang == "kn":
            if "fire" in emergency_type.lower():
                return [
                    "ಹೊಗೆಯಿಂದ ತಪ್ಪಿಸಿಕೊಳ್ಳಲು ನೆಲದ ಮೇಲೆ ತೆವಳಿ — ನೆಲದ ಬಳಿ ಶುದ್ಧ ಗಾಳಿ ಇರುತ್ತದೆ.",
                    "ಯಾವುದೇ ಕಾರಣಕ್ಕೂ ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ; ತುರ್ತು ಮೆಟ್ಟಿಲುಗಳನ್ನು ಮಾತ್ರ ಬಳಸಿ.",
                    "ಬೆಂಕಿ ಹರಡುವುದನ್ನು ತಡೆಯಲು ಹೊರಬರುವಾಗ ಬಾಗಿಲುಗಳನ್ನು ಮುಚ್ಚಿ.",
                    "ಬಟ್ಟೆಗೆ ಬೆಂಕಿ ಹೊತ್ತಿಕೊಂಡರೆ: ನಿಲ್ಲಿ, ನೆಲದ ಮೇಲೆ ಮಲಗಿ, ಉರುಳಿ (Stop, Drop, Roll).",
                ]
            elif "flood" in emergency_type.lower():
                return [
                    "ಹರಿಯುವ ಪ್ರವಾಹದ ನೀರಿನಲ್ಲಿ ನಡೆಯಲು ಅಥವಾ ವಾಹನ ಚಲಾಯಿಸಲು ಪ್ರಯತ್ನಿಸಬೇಡಿ.",
                    "ನೀರಿನಲ್ಲಿ ಮುಳುಗಿರುವ ವಿದ್ಯುತ್ ತಂತಿಗಳು ಮತ್ತು ತೆರೆದ ಮ್ಯಾನ್‌ಹೋಲ್‌ಗಳ ಬಗ್ಗೆ ಎಚ್ಚರವಿರಲಿ.",
                    "ರಕ್ಷಣಾ ತಂಡ ಬರುವವರೆಗೆ ಸುರಕ್ಷಿತ ಎತ್ತರದ ಸ್ಥಳದಲ್ಲಿ ಅಥವಾ ಮಹಡಿಯ ಮೇಲೆ ಇರಿ.",
                ]
            else:
                return [
                    "ಬೆಂಕಿ ಅಥವಾ ಸ್ಫೋಟದ ಅಪಾಯವಿಲ್ಲದಿದ್ದರೆ ಗಾಯಾಳುಗಳನ್ನು ಸ್ಥಳಾಂತರಿಸಬೇಡಿ.",
                    "ರಸ್ತೆ ಸಂಚಾರದಿಂದ ದೂರವಿದ್ದು ಸುರಕ್ಷಿತ ಸ್ಥಳದಲ್ಲಿ ನಿಲ್ಲಿರಿ.",
                    "ಆಂಬ್ಯುಲೆನ್ಸ್ ವಾಹನದ ಸುಲಭ ಪ್ರವೇಶಕ್ಕಾಗಿ ರಸ್ತೆಯನ್ನು ಮುಕ್ತವಾಗಿಡಿ.",
                ]

        elif lang == "ml":
            if "fire" in emergency_type.lower():
                return [
                    "പുകയിൽ നിന്ന് രക്ഷപ്പെടാൻ നിലത്തു കിടന്ന് ഇഴഞ്ഞു നീങ്ങുക.",
                    "ഒരു കാരണവശാലും ലിഫ്റ്റുകൾ ഉപയോഗിക്കരുത്; എമർജൻസി സ്റ്റെയർകേസ് ഉപയോഗിക്കുക.",
                    "തീ പടരാതിരിക്കാൻ വാതിലുകൾ അടച്ച് പുറത്തു കടക്കുക.",
                ]
            elif "flood" in emergency_type.lower():
                return [
                    "ഒഴുക്കുള്ള വെള്ളത്തിലൂടെ നടക്കാനോ വാഹനം ഓടിക്കാനോ ശ്രമിക്കരുത്.",
                    "വെള്ളത്തിനടിയിലുള്ള വൈദ്യുത കമ്പികളെയും മാൻഹോളുകളെയും കുറിച്ച് ജാഗ്രത പാലിക്കുക.",
                ]
            else:
                return [
                    "തീപിടുത്തമോ സ്ഫോടന സാധ്യതയോ ഇല്ലെങ്കിൽ പരിക്കേറ്റവരെ മാറ്റാൻ ശ്രമിക്കരുത്.",
                    "ആംബുലൻസിന്റെ സുഗമമായ യാത്രയ്ക്കായി വഴി ഒഴിഞ്ഞു കൊടുക്കുക.",
                ]

        # English (default)
        if "fire" in emergency_type.lower():
            return [
                "Crawl low under smoke — clean breathable air remains within 1 foot of the floor.",
                "Do NOT use elevators under any circumstances; use external fire exit stairwells.",
                "Close internal doors behind you as you evacuate to compartmentalize fire spread.",
                "If clothes catch fire: Stop, Drop, and Roll immediately.",
            ]
        elif "flood" in emergency_type.lower():
            return [
                "Do NOT attempt to walk, wade, or drive through flowing flood waters.",
                "Beware of hidden open manholes and live electrical cables in submerged areas.",
                "Stay on stable rooftop or elevated ground until emergency rescue teams arrive.",
            ]
        elif "cardiac" in emergency_type.lower():
            return [
                "Continue uninterrupted chest compressions at 100–120 beats per minute until paramedics arrive.",
                "Push hard and fast in the center of the chest (at least 2 inches deep).",
                "Send a bystander immediately to locate the nearest Automated External Defibrillator (AED).",
            ]
        else:
            return [
                "Do NOT move injured casualties unless there is immediate risk of fire or vehicle explosion.",
                "Stay safely behind the highway crash barrier away from moving corridor traffic.",
                "Keep the emergency breakdown shoulder completely clear for incoming ALS ambulances.",
            ]

    @classmethod
    def get_english_dispatch_summary(
        cls,
        text: str,
        emergency_type: str,
        location: Optional[str] = None,
        injuries: int = 0,
        affected_people: int = 0,
        indicators: Optional[List[str]] = None,
        lang: str = "en",
    ) -> str:
        """
        Synthesizes / translates a standardized English CAD dispatch narrative.
        Guarantees that control rooms, dispatchers, and responders receive strictly English output,
        regardless of whether citizen reports are submitted in Telugu, Tamil, Hindi, Kannada, or Malayalam.
        """
        if lang == "en":
            return text

        loc_str = f" at {location}" if location and location != "Location Unspecified" else ""
        cas_str = f"{injuries} casualty(ies) reported" if injuries > 0 else (
            f"{affected_people} individual(s) affected" if affected_people > 0 else "No immediate casualties reported"
        )
        ind_str = f" Critical factors: {', '.join(indicators)}." if indicators else ""

        return (
            f"CAD Dispatch: {emergency_type}{loc_str}. "
            f"{cas_str}.{ind_str} Priority responder deployment required."
        )

    @classmethod
    def get_role_intelligence(
        cls,
        role: str,
        emergency_type: str,
        injuries: int,
        affected_people: int,
        priority_score: int,
        lang: str = "en",
    ) -> Dict[str, any]:
        """
        Returns role intelligence for emergency control rooms.
        Control rooms and responder units strictly receive standardized English output,
        ensuring cross-jurisdictional clarity without translation delay or language barriers.
        """
        role = role.upper()

        # Control rooms strictly receive professional English directives
        if role == "HOSPITAL":
            summary = f"Level-1 trauma response for {emergency_type} with {injuries} reported injuries and priority {priority_score}/100."
            recommendation = "Clear trauma resuscitation bay, alert on-duty trauma surgical team, and prepare receiving ramp for incoming ALS units."
            checklist = [
                f"Reserve {max(1, injuries)} trauma resuscitation bay(s) with suction and airway management.",
                "Notify Alpha Surgical Team and Orthopedic on-call specialists.",
                "Prepare blood bank type O-negative cross-match protocol.",
                "Verify ventilator and monitor availability in trauma ICU.",
            ]
        elif role == "POLICE":
            summary = f"Corridor security and traffic dispatch for {emergency_type} at priority {priority_score}/100."
            recommendation = "Dispatch patrol unit to secure incident perimeter, stage traffic diversions upstream, and preserve emergency corridor for EMS."
            checklist = [
                "Deploy patrol unit to establish outer safety cordon 100 meters upstream.",
                "Place traffic cones and divert arterial lanes away from the impact site.",
                "Preserve active lane for incoming ambulance and fire tenders.",
                "Document scene telemetry and assist triage staging.",
            ]
        elif role == "FIRE":
            summary = f"Tactical rescue & hazard suppression for {emergency_type} at priority {priority_score}/100."
            recommendation = "Deploy Heavy Rescue Tender with hydraulic extrication gear, establish 360-degree hazard perimeter, and scan for hazardous materials."
            checklist = [
                "Stage rescue tender upwind with water and AFFF foam readiness.",
                "Deploy hydraulic cutters and spreaders for casualty extrication if trapped.",
                "Disconnect vehicle batteries to prevent electrical ignition.",
                "Establish isolation perimeter and verify structural stability.",
            ]
        else:
            summary = f"Multi-agency operational alert for {emergency_type} at priority {priority_score}/100."
            recommendation = "Maintain unified incident command and coordinate cross-agency resource deployment."
            checklist = [
                "Verify incident coordinates and triage status.",
                "Confirm casualty counts and staging locations.",
                "Synchronize CAD dispatch timeline across Police, Fire, and EMS.",
            ]

        return {
            "summary": summary,
            "recommendation": recommendation,
            "operational_checklist": checklist,
            "language": "en",
        }

