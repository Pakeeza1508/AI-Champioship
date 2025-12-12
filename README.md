# ✈️ FutureCraft - AI-Powered Aerospace CAD Web Application



A full-stack web application that generates, optimizes, and exports 3D CAD models of aerospace components using AI and real-world physics simulation.

**🎯 Try it live:** [FutureCraft App](https://ai-champioship.vercel.app/)  


## Tech Stack

### Frontend
- **SvelteKit** - Full-stack Svelte framework with routing and SSR
- **Threlte** - Declarative Three.js integration for Svelte
- **Three.js** - 3D rendering engine (WebGL)
- **TypeScript** - Type-safe development

### Backend
- **Python 3.10+** - Backend runtime
- **FastAPI** - High-performance async API framework
- **Cerebras Cloud SDK** - Ultra-fast LLM inference for parameter extraction
- **Trimesh** - 3D mesh processing and STL export
- **NumPy/SciPy** - Physics calculations and structural analysis

### Infrastructure & Cloud
- **Vercel** - Frontend hosting and deployment
- **Hugging Face Spaces** - Backend API hosting (Docker)
- **Vultr** - Cloud compute infrastructure
- **Raindrop** - Object storage for CAD files and assets


## ✨ Features

### Core Capabilities
- 🤖 **AI-Powered Design**: Natural language to parametric 3D models using Cerebras LLM
- 🎨 **Real-Time 3D Viewer**: Interactive WebGL-based component visualization
- 🔧 **Parametric Controls**: Live dimension editing with instant visual feedback
- 🧪 **Physics Simulation**: Structural stress analysis, safety factors, and material properties
- 📊 **Materials Database**: Al7075, Titanium, Carbon Fiber with real-world properties
- 🌍 **Mission Profiles**: Altitude/speed simulation with atmospheric physics
- 💬 **AI Chat Assistant**: Conversational interface for design modifications
- 📦 **CAD Export**: STL format for 3D printing and manufacturing
- 🛡️ **Auto-Optimization**: AI agent corrects designs to meet safety standards

### Supported Components
- Wings (swept, delta, straight)
- Fuselage (commercial, fighter, cargo)
- Engines (jet, turboprop)

## Quick Start
20+ and npm
- Python 3.10+
- Cerebras API key ([Get one free here](https://cloud.cerebras.ai))d npm/pnpm
- Python 3.11+
- OpenAI API key

### Setup

1. **Clone and navigate to project**
```bash
cd futureCraft
```

2. **Set up backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate 
 # On Windows: 
 venv\Scripts\activate
pip install -r requirements.txt

# Add your CEREBRAS API key to .env (get it from https://cloud.cerebras.ai)
```

3. **Set up frontend**
```bash
cd ../frontend
npm install
```

4. **Run development servers**

Terminal 1 (Backend):
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

5. **Open browser**
Navigate to `http://localhost:5173`


## Architecture

### Text-to-3D Pipeline
1. User enters text description (e.g., "Create a Boeing 747 commercial airliner")
2. FastAPI routes request to Cerebras LLM with aerospace engineering context
3. AI extracts structured parameters (wing span, sweep angle, materials, etc.)
4. Geometry service generates parametric 3D mesh using Trimesh
5. Physics engine calculates volume, stress, and safety factors
6. Frontend receives mesh + metadata and renders with Threlte/Three.js
7. User adjusts parameters via sliders or chat with instant visual updates

### Data Flow
```
User Input (Text/Image)
    ↓
Frontend (SvelteKit)
    ↓
API (FastAPI)
    ↓
AI Service (OpenAI) → Parameters
    ↓
Geometry Service → 3D Mesh
    ↓
Export Service → CAD Files
    ↓
Frontend (Threlte) → 3D Viewer
```
🎯 Project Status

**Deployed:**
- Frontend: Vercel (CDN)
- Backend: Hugging Face Spaces (Docker container)
- Infrastructure: Vultr (cloud compute)
- Storage: Raindrop (object storage)
AeroCraft](https://github.com/snowcodeer/AeroCraft) by snowcodeer.

We gratefully acknowledge their work in establishing the initial:
- Text-to-3D LLM integration pipeline
- Base parametric mesh generation logic
- Three.js viewer setup

All original code remains credited under their MIT license
## 📄 What's New in FutureCraft

This project significantly extends the original open-source prototype with production-ready features:

| Feature Category | Original Base | **FutureCraft Enhancement** |
|---|---|---|
| **Physics Engine** | None (visual only) | ✅ Real structural simulation with beam theory, stress analysis, and safety factors |
| **Materials System** | Generic mesh | ✅ Engineering materials database (Al7075, Ti-6Al-4V, CFRP) with real density/strength |
| **Mission Profiles** | None | ✅ Altitude/speed environment simulation with atmospheric physics and Mach calculations |
| **AI Intelligence** | Basic text-to-shape | ✅ AI optimization agent that auto-corrects unsafe designs |
| **Backend** | Prototype with bugs | ✅ Production FastAPI with async fixes, O(1) volume calc, proper error handling |
| **Frontend** | Basic viewer | ✅ Professional UI with Mission Control, parametric sliders, and chat interface |
| **Deployment** | Local only | ✅ Cloud deployment (Vercel + Hugging Face) with CI/CD |
| **LLM Provider** | OpenAI (paid) | ✅ Cerebras Cloud (free tier, 10x faster inference) |

---

**Built with ❤️ for aerospace engineering and AI innovation**