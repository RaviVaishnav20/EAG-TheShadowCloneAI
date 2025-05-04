# 🚀 VectorDB Assistant – Chrome Extension

Bring AI-powered memory to your browser.

## 🔍 What is VectorDB Assistant?

VectorDB Assistant is a Chrome extension that helps you **capture, search, and interact** with the content you care about—using the power of semantic search and contextual AI.

### Key Highlights:

* 📝 **Save** text, full web pages, PDFs, or custom snippets to a vector database
* 🔎 **Search** semantically across your saved content
* 🤖 **Ask Nimo**, your AI assistant, to answer questions using your stored knowledge

---

## ✨ Features

### 📥 Save Content

* Save selected text via context menu
* Capture entire web pages with one click
* Upload and index PDF documents
* Manually input custom text snippets

### 🔍 Semantic Search

* AI-powered search across all your content
* Adjustable result count
* Relevance-based scoring for better answers

### 🤖 Ask Nimo

* Get intelligent answers using your saved data
* Ask questions in natural language
* Receive context-aware, helpful responses

---

## ⚙️ Requirements

* Chrome browser (v88+)
* Backend APIs:

  * **VectorDB API** (`http://localhost:8000`)
  * **Nimo Agent API** (`http://localhost:8002`)

---

## 🧰 Installation

1. **Clone** or **download** this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Toggle on **Developer Mode** (top-right)
4. Click **Load unpacked**, then select the project folder

---

## 🔧 Backend Setup

### 🧠 VectorDB API

Required endpoints:

* `POST /ingest/text` — Save text
* `POST /ingest/pdf` — Save PDF
* `POST /ingest/url` — Save URL
* `POST /search` — Semantic search
* `GET /health` — Health check

### 🗨️ Nimo Agent API

Required endpoint:

* `POST /agent` — Ask questions, get answers

---

## 🚀 Usage Guide

1. Click the extension icon in Chrome
2. Use tabs to navigate:

   * **Save**: Add text, PDFs, or current URL
   * **Search**: Explore saved content
   * **Ask Nimo**: Interact with your AI assistant

### Right-Click Menu

Easily save selected text via **"Save selection to VectorDB"** in the context menu.

---

## ⚙️ Configuration

Update API endpoints in `popup.js` if needed:

```js
const API_ENDPOINTS = {
  ingestText: 'http://localhost:8000/ingest/text',
  ingestPdf: 'http://localhost:8000/ingest/pdf',
  ingestUrl: 'http://localhost:8000/ingest/url',
  search: 'http://localhost:8000/search',
  askNimo: 'http://localhost:8002/agent'
};
```

---

## 🛠 Troubleshooting

* **APIs not responding?**
  → Check that both services are running and review browser console logs

* **Permission issues?**
  → Confirm `manifest.json` includes correct host permissions

* **Save failures?**
  → Inspect backend logs or check for data limits

---

## 👨‍💻 Development Workflow

1. Modify code as needed
2. Go to `chrome://extensions/`
3. Hit **Refresh** on your extension card to reload


