# 👔 Wardrobe Stylist

**Wardrobe Stylist** is a smart, local web-based agentic application that helps users decide what to wear — powered by **GPT-4o-mini** (deployed on Azure OpenAI), Azure’s **Computer Vision API**, and an MCP-inspired architecture.

Users simply upload photos of their clothing, and the app automatically generates detailed descriptions (color, fit, style, season, etc.). Then, when prompted with questions like **“What should I wear today?”**, the system uses Azure OpenAI, real-time weather data **(Toronto, Ontario, Canada)**, and the wardrobe context to recommend the perfect outfit.

All of this happens through a friendly browser-based interface that runs locally via FastAPI — no internet deployment required.

---

![example1](https://github.com/user-attachments/assets/13c27c5f-a429-4bd5-a30c-7fb49e37a421)

## ✨ Features

- 🧺 Upload clothing images and auto-generate rich descriptions
- 👁️ Built-in visual pipeline using OpenAI vision models
- 🧠 Wardrobe stored as NDJSON, queried with an MCP-inspired approach
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

### 3. Add your credientials in `ai_hackathon.env`

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
 ┗ 📄 ai_hackathon.env
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



## 🗂️ Data
This project uses a publicly available dataset from Kaggle as example clothing images to simulate a user's wardrobe.
You can find the dataset here:
https://www.kaggle.com/datasets/agrigorev/clothing-dataset-full

---

## 🔒 Disclaimer

This project runs locally and your data stays private. Your `.env` file is not committed and should remain secret.

---

## ℹ️ About the MCP-inspired Architecture
This project incorporates principles of a Model Context Protocol (MCP) to manage the wardrobe data effectively.  Specifically:
- Structured Storage: Wardrobe data is stored in NDJSON, providing a structured and easily parseable format.
- Custom Querying: The mcp_store.py module implements custom logic to query this NDJSON data, allowing the agent to retrieve relevant clothing information.


Note: While the architecture emphasizes separation and structured access to context, it does not currently expose a standardized HTTP contract for automatic model integration.  Future development may explore this to enhance modularity.

---

## Special Thanks

Thank you for the idea from the following amazing people:

- [Ethan Hu] (https://www.linkedin.com/in/48471820b/)
- [Christine Tang] (https://www.linkedin.com/in/c-christine-tang/)
- [Allan Galli Francis] (https://www.linkedin.com/in/allangallifrancis/)


