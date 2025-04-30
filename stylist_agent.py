# stylist_agent.py
# -----------------------------------------------------------
# Chat-over-context “Wardrobe Stylist”                    v3
# -----------------------------------------------------------
import os, json, sys, requests
from typing import List, Dict
from dotenv import load_dotenv

from langchain.tools          import tool
from langchain_openai         import AzureChatOpenAI
from langchain.agents         import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts   import ChatPromptTemplate, MessagesPlaceholder

# ── MCP data ------------------------------------------------
from mcp_store import load_wardrobe          # local NDJSON
# from mcp_client import load_wardrobe       # HTTP API

load_dotenv("ai_hackathon.env", override=True)

# ── TOOLS ---------------------------------------------------
@tool
def get_user_wardrobe() -> List[Dict]:
    """Return the user’s wardrobe as a JSON list."""
    return load_wardrobe()

@tool
def get_weather(city: str) -> Dict:
    """Return tomorrow’s min/max °C for the city (Open-Meteo)."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=43.7&longitude=-79.4"       # Toronto
        "&daily=temperature_2m_min,temperature_2m_max"
        "&timezone=America%2FToronto"
    )
    daily = requests.get(url, timeout=10).json()["daily"]
    return {"city": city,
            "t_min": daily["temperature_2m_min"][1],
            "t_max": daily["temperature_2m_max"][1]}

tools = [get_user_wardrobe, get_weather]

# ── PROMPT --------------------------------------------------
schema = {
    "type": "object",
    "properties": {
        "occasion":   {"type": "string"},
        "items":      {"type": "array", "items": {"type": "string"}},
        "files":      {"type": "array", "items": {"type": "string"}},
        "commentary": {"type": "string"}
    },
    "required": ["occasion", "items", "files", "commentary"]
}

def _escape_curly(txt: str) -> str:
    """Escape braces so the template engine ignores them."""
    return txt.replace("{", "{{").replace("}", "}}")

schema_block = _escape_curly(json.dumps(schema, indent=2))

SYSTEM_MSG = f"""
You are a personal stylist.

* Always call tools when you need the wardrobe or the weather.
* Recommend **only** items that really exist in the wardrobe list.
* For every recommended item, include the matching `source_image`
  filename in the **files** array, in the same order as **items**.
* Your final answer must be **exactly** one JSON object matching:
{schema_block}
"""

prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_MSG.strip()),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ]
)

# ── LLM -----------------------------------------------------
llm = AzureChatOpenAI(
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
    openai_api_key  = os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint  = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version     = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    temperature     = 0.2,
    model_kwargs    = {"response_format": {"type": "json_object"}},  # pure JSON
)

# ── AGENT ---------------------------------------------------
agent_runnable = create_openai_tools_agent(llm, tools, prompt=prompt)
stylist = AgentExecutor(
    agent          = agent_runnable,
    tools          = tools,
    verbose        = True,
    max_iterations = 4,          # stop before any infinite loop
)

# ── Helper: pretty print -----------------------------------
def pretty_print(reply: Dict) -> str:
    """
    Turn the JSON reply into a neat console block.
    Falls back to a lookup if the model (ever) omits `files`.
    """
    if "files" in reply and reply["files"]:
        file_list = reply["files"]
    else:
        # fallback: derive files from wardrobe
        wardrobe = load_wardrobe()
        lookup = {r["item"].lower(): r.get("source_image", "?")
                  for r in wardrobe}
        file_list = [lookup.get(i.lower(), "?") for i in reply["items"]]

    lines = [
        f"Occasion :  {reply['occasion']}",
        f"Items    :  {', '.join(reply['items'])}",
        f"Files    :  {', '.join(file_list)}",
        f"Notes    :  {reply['commentary']}",
    ]
    return "\n".join(lines)

# ── REPL ----------------------------------------------------
if __name__ == "__main__":
    print("👗  Wardrobe Stylist — ask me what to wear!  (Ctrl-C to quit)")
    while True:
        try:
            user_q = input("\nYou: ").strip()
            if not user_q:
                continue

            result = stylist.invoke({"input": user_q})
            raw = result["output"]                     # JSON string from LLM

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print("Assistant (raw):", raw)
                continue

            print("\nAssistant:\n" + pretty_print(data))

        except KeyboardInterrupt:
            sys.exit(0)