# 👔 Wardrobe Stylist

**Wardrobe Stylist** is a smart, local web-based agentic application that helps users decide what to wear — 
powered by **GPT-4o-mini**, computer vision, and **Model Context Protocol (MCP)**.

Users simply upload photos of their clothing, and the app automatically generates detailed descriptions (color, fit, style, season, etc.). Then, when prompted with questions like **“What should I wear today?”**, the system uses Azure OpenAI, real-time weather data, and the wardrobe context to recommend the perfect outfit.

All of this happens through a friendly browser-based interface that runs locally via FastAPI — no internet deployment required.

---
![example1](https://github.com/user-attachments/assets/be8d4cdf-82fe-4fc8-a3d2-7b5898c697a4)

## ✨ Features

- 🧺 Upload clothing images and auto-generate rich descriptions
- 👁️ Built-in visual pipeline using OpenAI vision models
- 🧠 Wardrobe stored as NDJSON, queried with Model Context Protocol
- 💬 Chat-style web interface built with FastAPI + JavaScript
- 🌦️ Recommendations based on:
  - Your wardrobe
  - Local weather in Toronto
  - The occasion (e.g., work, gym, party)

---

## 🚀 Getting Started

### 1. Clone this repo

```bash
git clone https://github.com/yourusername/wardrobe-stylist.git
cd wardrobe-stylist
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your `.env`

```dotenv
AZURE_VISION_ENDPOINT=https://YOUR-RESOURCE-NAME.cognitiveservices.azure.com/
AZURE_VISION_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE-NAME.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
OPENAI_API_VERSION=2024-08-01-preview
```

### 4. Run the app

```bash
uvicorn main:app --reload
```

Then open your browser at [http://localhost:8000](http://localhost:8000). If that doesn't work, check your terminal for the actual running port.

---

## 📁 Project Structure

```
📦 wardrobe-stylist/
 ┣ 📁 static/               # JS and CSS
 ┃ ┗ 📄 chat.js
 ┣ 📁 templates/            # HTML templates
 ┃ ┗ 📄 index.html
 ┣ 📁 User Weardrobe/       # Uploaded images
 ┣ 📄 main.py               # FastAPI app
 ┣ 📄 clothing_vision.py    # Vision → description pipeline
 ┣ 📄 stylist_agent.py      # Outfit recommendation agent
 ┣ 📄 mcp_store.py          # Wardrobe memory via NDJSON
 ┣ 📄 requirements.txt
 ┗ 📄 .env                  # Your credentials (not committed)
```

---

## 🧠 Powered By

- Python + FastAPI
- Azure OpenAI GPT-4o (Vision + Function Calling)
- OpenAI Vision API for clothing analysis
- Model Context Protocol (LangChain)
- Tiktoken + NDJSON for wardrobe memory
- HTML/CSS/JS for local frontend

---

## 💡 Tip

After uploading your images, the app will process them automatically. Once it says _“✅ Finished processing - ask me what to wear!”_, the stylist is ready to chat!

---

## 🔒 Disclaimer

This project runs locally and your data stays private. Your `.env` file is not committed and should remain secret.

---

## Special Thanks

Thank you for the idea from the following amazing people:

- [Ethan Hu] (https://www.linkedin.com/in/48471820b/)
- [Christine Tang] (https://www.linkedin.com/in/c-christine-tang/)
- [Allan Galli Francis] (https://www.linkedin.com/in/allangallifrancis/)
