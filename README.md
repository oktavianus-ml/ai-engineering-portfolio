# 👨‍💻 AI Engineering Portfolio
**LLM • RAG • Forecasting • Decision Intelligence**

I am an AI Engineer specializing in **Enterprise-grade LLM systems**, with a focus on **Retrieval-Augmented Generation (RAG)** and **forecasting-driven decision support.

This repository showcases **production-oriented AI systems** with clear architecture, representative core code, and real-world use cases.

⚠️ Note: Code shown is **representative core logic only. Some components are simplified or redacted for confidentiality.

---

## 🚀 Featured Projects


1️⃣ Enterprise RAG FAQ System – CNI AI Chatbot
**Category:** Conversational AI · RAG · Knowledge Systems  
**Role:** AI Engineer / System Designer  

An **enterprise FAQ chatbot** powered by **Retrieval-Augmented Generation (RAG)** to provide **accurate, grounded, and auditable answers** from internal knowledge sources.

### 🔍 Business Problem
- Enterprise knowledge is distributed across multiple documents
- Manual support processes are inefficient
- Risk of hallucination in generic LLM-based chatbots

### 💡 Solution
Designed and implemented a **RAG-based chatbot system** that:
- Retrieves relevant internal documents using embeddings
- Grounds LLM responses on verified knowledge sources
- Exposes REST APIs for enterprise system integration


### 🏗 Architecture Overview
The system is designed as a **modular Enterprise RAG (Retrieval-Augmented Generation) architecture**, separating concerns between **API layer, core reasoning engine, ingestion pipeline, and data layer**.

User / Channel (Web, Telegram)
↓
API Layer (FastAPI)
↓
Router & Policies
↓
RAG Core Engine
├─ Retriever (Vector Search)
├─ Context Builder
├─ Prompt Builder
└─ LLM Caller
↓
LLM (Local / Ollama)
↓
Final Answer + Confidence


## 📂 Project Structure (Simplified)

cni-ai-chatbot/
├── api/ # API & routing layer
├── core/ # RAG reasoning engine
├── ingestion/ # Document chunking & embedding
├── loaders/ # PDF / Web loaders
├── retriever.py # Semantic retrieval
├── call_llm.py # LLM abstraction
├── ollama.py # Local LLM integration
├── README.md
├── requirements.txt
└── Dockerfile



#### 1️⃣ API & Interface Layer
Handles all external interactions and request validation.

- `api/main.py` – Application entry point  
- `api/router.py` – Request routing  
- `telegram_bot.py` – Telegram integration  
- `schemas.py` – Request/response schema  

This layer ensures **clean separation between interface and core logic**.


#### 2️⃣ Ingestion & Knowledge Processing
Responsible for converting raw enterprise documents into searchable knowledge.

- `loaders/` – PDF, web, image loaders  
- `ingestion/chunker.py` – Document chunking  
- `ingestion/embedder.py` – Embedding generation  
- `scripts/embed_*.py` – Batch ingestion pipelines  

Outputs are stored in a **vector store** for semantic retrieval.

---

#### 3️⃣ Retrieval & Search Layer
Fetches relevant knowledge based on semantic similarity.

- `retriever.py` – Vector-based retrieval  
- `search.py` – Query execution  
- `vector_store/` – Embedded knowledge storage  

This layer ensures **answers are grounded in verified documents**.

---

#### 4️⃣ RAG Core Reasoning Engine
The heart of the system that composes context and controls reasoning.

- `core/engine.py` – Main RAG execution flow  
- `context_builder.py` – Context assembly  
- `prompt_builder.py` – Prompt construction  
- `composer.py` – Multi-source answer composition  
- `policies.py` – Answer control & guardrails  
Designed to **minimize hallucination and enforce consistency**.


#### 5️⃣ LLM Integration Layer
Abstracted interface to LLM providers.

- `call_llm.py` – Unified LLM interface  
- `ollama.py` – Local model execution  
- `sop_llm.py` – SOP-aware prompting  
Allows **model swapping without changing core logic**.


#### 6️⃣ Learning & Feedback Loop (Optional)
Enables system improvement over time.

- `learning.py` – Learning logic  
- `confidence.py` – Answer confidence scoring  
- `data/json/chat_logs.jsonl` – Interaction logs  
Supports **continuous improvement and auditability**.


#### 7️⃣ Data Layer
Stores raw, processed, and learned knowledge.
- `data/raw/` – Source documents  
- `data/processed/` – Cleaned content  
- `data/vectorstore/` – Embeddings  
- `learned_answers.json` – Accepted answers  

---

### ✅ Architectural Highlights

- Modular, production-oriented design  
- Clear separation of concerns  
- RAG-first approach to reduce hallucination  
- Scalable ingestion and retrieval pipeline  
- LLM-agnostic integration  


### 🧠 Key Capabilities
- Document ingestion & vector embedding
- Semantic search using vector database
- Prompt engineering with contextual grounding
- Modular service-based architecture

### 🛠 Tech Stack
- **Language:** Python  
- **Frameworks:** FastAPI  
- **AI:** LLM, RAG, Embeddings  
- **Tools:** Docker, Git  

📂 Project Folder: `projects/enterprise-knowledge-chatbot-rag`


######################################################################################


2️⃣ Forecasting Decision Assistant (LLM + Time Series)

**Category:** Decision Intelligence · Forecasting · AI Assistant  
**Role:** Machine Learning / AI Engineer  

An **AI-powered decision assistant** that combines **time-series forecasting models** with **LLM-based reasoning** to support operational and strategic decisions.

### 🔍 Business Problem
- Forecast outputs are difficult for non-technical stakeholders to interpret
- Decision-makers need explanations, not just numeric predictions
- Lack of intelligent interface for forecasting insights

### 💡 Solution
Built a system that:
- Generates forecasts from historical time-series data
- Evaluates model performance using standard metrics
- Uses LLM to translate forecasts into natural-language insights

### 📐 Models & Methods
- Statistical and ML time-series models (ARIMA, Prophet, etc.)
- Forecast evaluation (RMSE, MAE)
- LLM-based explanation and insight generation

### 🛠 Tech Stack
- **Language:** Python  
- **ML:** Time Series Forecasting  
- **AI:** LLM-based reasoning  
- **Tools:** Jupyter, Scikit-learn  

📂 Project Folder: `projects/..`

---

## 🛠 Core Skills Demonstrated

- Enterprise LLM System Design  
- Retrieval-Augmented Generation (RAG)  
- Time Series Forecasting  
- API-based AI Services  
- Clean and scalable project architecture  
- AI systems with business impact  

---

## 🧭 Why This Portfolio

✔ Built with **real-world enterprise use cases**  
✔ Focused on **architecture, reasoning, and impact**  
✔ Clean, readable, and production-minded code  
✔ Scalable structure for future AI projects  

---

## 📬 Contact

📧 Email: your@email.com  
💼 LinkedIn: your-linkedin-url  
