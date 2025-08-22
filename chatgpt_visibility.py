import os
from dotenv import load_dotenv
from openai import OpenAI

# ==========================================================================
# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================================================
# Log

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# ==========================================================================
# Load prompt.json file

def load_prompts_from_json(json_path: str = '') -> Dict[str, Any]:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    except FileNotFoundError:
        logging.error(f"Prompt configuration file not found at {json_path}. Please ensure the file exists.")
        return {}
    
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding prompt configuration JSON: {e}")
        return {}


# ==========================================================================
# json

def extract_json_block(raw: str) -> str:
    m = re.search(r"```json\s*({.*?})\s*```", raw, flags = re.S)
    if m:
        return m.group(1)
    
    m = re.search(r"```\s*({.*?})\s*```", raw, flags=re.S)
    if m:
        return m.group(1)
    
    m = re.search(r"({.*})", raw, flags=re.S)
    if m:
        return m.group(1)
    
    return ""

# ==========================================================================
# Normalize sources

def normalize_sources(sources: Any) -> List[Dict[str, str]]:
    norm = []
    if not sources:
        return norm

    if isinstance(sources, str):
        return [{'URL': sources}]
    
    if isinstance(sources, list):
        for s in sources:
            if isinstance(s, str):
                norm.append({'URL': s})
            elif isinstance(s, dict):
                url = s.get("URL") or s.get("url") or s.get("link")
                if url:
                    norm.append({'URL': url})
    
    return norm


# ==========================================================================
