# FutureCraft - AI-Powered Aerospace CAD Web Application

A full-stack web application for generating, modifying, and exporting 3D CAD models of aerospace components using AI.
- Demo video: https://youtu.be/xMromFDNgXw

## Tech Stack

### Frontend
- **SvelteKit** - Full-stack Svelte framework with routing and SSR
- **Threlte** - Declarative Three.js integration for Svelte
- **Three.js** - 3D rendering engine (WebGL)
- **TypeScript** - Type-safe development

### Backend
- **Python 3.11+** - Backend runtime
- **FastAPI** - High-performance async API framework
- **OpenAI API** - GPT-4 for parameter extraction, DALL-E for image processing
- **Trimesh** - 3D mesh processing and STL export
- **pythonOCC** - OpenCascade wrapper for STEP/IGES export


## Features

### MVP (Phase 1)
- ✅ Text-to-3D generation (natural language → parametric models)
- ✅ Image reference viewer (upload and display reference images)
- ✅ Parametric controls (real-time dimension editing)
- ✅ CAD export (STL, STEP, IGES formats)

### Future Enhancements
- Image-to-3D reconstruction
- Version control and revision history
- Collaborative editing
- Cloud storage integration
- Advanced aerodynamic analysis
- Multi-part assemblies

## Quick Start

### Prerequisites
- Node.js 18+ and npm/pnpm
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
1. User enters text description (e.g., "delta wing with 45° sweep, 2m span")
2. FastAPI sends to OpenAI GPT-4 with aerospace engineering prompt
3. GPT-4 extracts structured parameters (wing type, dimensions, angles)
4. Geometry service generates 3D mesh using parametric templates
5. Frontend receives mesh data and renders with Threlte
6. User can adjust parameters in real-time

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

## License

MIT

## 🤝 Acknowledgements & Attribution

**FutureCraft** is built upon the architectural foundation of [Original Project Name](https://github.com/snowcodeer/AeroCraft) by [snowcodeer].

We gratefully acknowledge their work in establishing the initial:
*   Text-to-3D LLM integration pipeline.
*   Base parametric mesh generation logic.
*   Three.js viewer setup.


## 🚀 Hackathon Implementation Details

This project extends an existing open-source prototype. Below is a breakdown of the original codebase versus our engineering contributions for this hackathon:

| Feature Category | Original Base Project | **New in FutureCraft (Our Work)** |
| :--- | :--- | :--- |
| **Physics Engine** | None (Visual only) | **Added Structural Simulation** (Beam Theory, Stress Analysis, Safety Factors). |
| **Materials** | None (Generic mesh) | **Added Material Database** (Al7075, Titanium, Carbon Fiber) with real density/strength properties. |
| **Environment** | None | **Added Mission Profile** (Altitude/Speed sliders, Atmospheric Physics, Mach calculation). |
| **Intelligence** | Text-to-Shape | **Added AI Optimization Agent** (Auto-corrects failed designs to meet safety standards). |
| **Assembly** | Basic Positioning | **Fixed & Enhanced** (Solved compilation bugs, added intelligent positioning logic). |
| **Architecture** | Async Logic Errors | **Refactored Backend** (Fixed async/await bugs, optimized volume calculation for O(1) performance). |