# Install required packages
#!pip install azure-cognitiveservices-vision-computervision openai python-dotenv tiktoken

import os, glob, time, json, re, logging, dotenv, tiktoken
from openai import AzureOpenAI
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ----------------- CONFIG -----------------
dotenv.load_dotenv("ai_hackathon.env", override=True)

IMAGE_DIR        = "User Weardrobe"               # folder with .jpg / .png
AGGREGATE_NDJSON = "closet.ndjson"            # final corpus
ALLOWED_EXT      = {".jpg", ".jpeg", ".png", ".webp"}
dir_name = os.path.dirname(AGGREGATE_NDJSON)
if dir_name:
    os.makedirs(dir_name, exist_ok=True)


# ---------- RATE-LIMIT BUCKET ----------
class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = capacity
        self.tokens   = capacity
        self.refill   = refill_rate_per_sec
        self.t0       = time.monotonic()

    def _leak(self):
        now = time.monotonic()
        leaked = (now - self.t0) * self.refill
        if leaked:
            self.tokens = min(self.capacity, self.tokens + leaked)
            self.t0 = now

    def consume(self, n: int):
        while True:
            self._leak()
            if self.tokens >= n:
                self.tokens -= n
                return
            time.sleep((n - self.tokens) / self.refill)

# Quotas
VISION_TPM = 20
GPT_TPM    = 1_000
vision_bucket = TokenBucket(VISION_TPM, VISION_TPM / 60)
gpt_bucket    = TokenBucket(GPT_TPM,    GPT_TPM  / 60)

# ---------- CLIENTS ----------
vision_client = ComputerVisionClient(
    os.getenv("AZURE_VISION_ENDPOINT"),
    CognitiveServicesCredentials(os.getenv("AZURE_VISION_KEY"))
)

gpt_client = AzureOpenAI(
    api_key       = os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint= os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version   = "2024-08-01-preview"
)
GPT_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ---------- PROMPT PARTS ----------
FIELD_GUIDE = (
    # Few-shot: give *illustrative* values, not a mandatory list
    "- item: e.g. t-shirt, jacket, dress\n"
    "- category: e.g. outerwear, activewear, loungewear\n"
    "- color: predominant color, e.g. navy blue, light-gray, bright-red\n"
    "- style: e.g. casual, formal, sporty, business\n"
    "- fit: e.g. slim, loose, oversized\n"
    "- suitable_seasons: e.g. summer, winter, all seasons\n"
    "- warmth_level: e.g. lightweight, insulated, heavy\n"
    "- coverage: e.g. full sleeves, sleeveless, cropped\n"
    "- water_resistant: yes / no, based on visual\n"
    "- clothing_features: e.g. hood, zipper, buttons, none\n"
    "- pattern_or_graphics: e.g. solid, striped, graphic print\n"
    "- suggested_occasions: e.g. gym, party, office, travel\n"
    "- layering_potential: e.g. base layer, standalone, overlayer\n"
    "- visual_description: 1–2 sentences describing **only the garment’s appearance** (ignore background, setting, people)\n"
    "- visible_accessories: e.g. scarf, belt, none"
)
SYSTEM_MSG = (
    "You are a fashion-metadata extractor. "
    "Return ONLY one JSON object with the 15 fields from the Field Guide. "
    "Do not wrap the output in markdown, code-fences, or explanations. "
    "`color` must be free-form text (no hex codes, no nested objects). "
    "`visual_description` must be a concrete sentence (≤ 30 words) about the garment **only—ignore background or setting**."
)


enc = tiktoken.encoding_for_model("gpt-4o-mini")

# ---------- HELPER ----------
def describe_image(image_path: str, *, max_retries: int = 2, backoff: float = 2.0) -> dict:
    """Vision ➜ GPT ➜ dict.  Retries on bad JSON; obeys rate limits."""
    # ----- VISION -----
    vision_bucket.consume(1)                                 # 20 calls/min guard
    with open(image_path, "rb") as stream:
        result = vision_client.analyze_image_in_stream(
            image=stream,
            visual_features=[VisualFeatureTypes.description, VisualFeatureTypes.tags],
        )
    caption = result.description.captions[0].text if result.description.captions else "No caption"
    tags    = ", ".join(t.name for t in result.tags)
    vision_summary = f"Caption: {caption}\nTags: {tags}"

    # ----- GPT -----
    base_prompt = f"{FIELD_GUIDE}\n\nVisual Info:\n{vision_summary}"
    prompt_tokens = len(enc.encode(base_prompt)) + len(enc.encode(SYSTEM_MSG))
    completion_cap = 180

    attempt = 0
    while attempt <= max_retries:
        attempt += 1

        # reserve tokens
        gpt_bucket.consume(prompt_tokens + completion_cap)

        chat_resp = gpt_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user",   "content": base_prompt}
            ],
            max_tokens=completion_cap
        )
        used_tokens = chat_resp.usage.total_tokens
        # refund unused allowance
        refund = (prompt_tokens + completion_cap) - used_tokens
        if refund > 0:
            gpt_bucket.consume(-refund)

        resp = chat_resp.choices[0].message.content

        # ----- scrub & parse -----
        match = re.search(r"\{.*\}", resp, flags=re.S)
        if not match:
            logging.warning("No JSON found, attempt %d/%d", attempt, max_retries)
        else:
            try:
                record = json.loads(match.group(0))
                record["source_image"] = os.path.basename(image_path)
                return record
            except json.JSONDecodeError as e:
                logging.warning("Bad JSON (%s), attempt %d/%d", e, attempt, max_retries)

        # retry
        if attempt <= max_retries:
            time.sleep(backoff * attempt)
        else:
            raw_file = image_path + ".gpt_raw.txt"
            with open(raw_file, "w") as f:
                f.write(resp)
            raise RuntimeError(f"Could not parse GPT JSON after {max_retries} retries; raw saved to {raw_file}")

# --- add at bottom of clothing_vision.py -------------------
if __name__ == "__main__":
    processed = 0
    image_paths = [
        p for ext in ALLOWED_EXT
        for p in glob.glob(os.path.join(IMAGE_DIR, f"*{ext}"))
    ]

    with open(AGGREGATE_NDJSON, "w") as ndjson_f:           # overwrite each run
        for img_path in sorted(image_paths):
            try:
                record = describe_image(img_path)
                ndjson_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                processed += 1
                print(f"✓ processed {img_path}")
            except Exception as e:
                print(f"⚠️  failed on {img_path}: {e}")

    print(f"\nFinished: {processed} images written to {AGGREGATE_NDJSON}")