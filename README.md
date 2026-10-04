# 🏠 Home Gennie — AI Interior Design & 3D/AR Platform

> **Transform real-world room photos into photorealistic, style-customized architectural designs while preserving exact room geometry, with instant 3D mesh reconstruction and mobile Augmented Reality (AR).**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_%2B_Uvicorn-009688.svg)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Database_%26_Auth-Supabase-3ecf8e.svg)](https://supabase.com/)

---

## 📖 Overview & Core Concepts

Most generative AI image models redesign rooms by generating entirely new spaces from scratch—hallucinating windows, shifting structural walls, and changing camera perspectives.

**Home Gennie** is designed around **geometric fidelity** and **spatial immersion**:
1. **Structural Preservation:** Extracts structural edge geometry (MLSD) and spatial depth maps from your uploaded room photo so walls, doors, windows, and ceiling lines remain fixed in space.
2. **Style Customization:** Applies designer styles (Modern, Minimalist, Scandinavian, Bohemian, Industrial, Japandi, and more) to furnishings, lighting, materials, and color palettes.
3. **Monocular 3D Reconstruction:** Converts the resulting 2D interior design into a fully textured 3D `.glb` room mesh using depth back-projection.
4. **Augmented Reality (AR):** View the 3D model interactively in your browser with Three.js / `<model-viewer>`, or project it directly onto your floor using WebXR (Android) and ARKit Quick Look (iOS) via mobile or QR code handoff.
5. **Asset Permanence:** Downloads all AI-generated assets directly to permanent cloud storage, preventing dead links caused by expiring third-party CDN URLs.

---

## ✨ Key Features

- 📸 **Room Photo Upload:** Simple drag-and-drop room image upload supporting standard formats (JPG, PNG, WebP).
- 🎨 **Multi-Style & Room Selection:** Choose from numerous styles and room categories (Living Room, Bedroom, Kitchen, Office, etc.) with custom preferences.
- 📐 **Geometry-Preserved Redesign:** Employs architectural line detection and depth conditioning so redesigns stay true to your actual floor plan.
- ⚡ **Non-Blocking Background Generation:** Requests return immediately with a processing status while generation runs asynchronously, keeping the interface fluid and responsive.
- 🧱 **One-Click 3D Mesh Generation:** Turn any redesign into an explorable 3D room model (.glb) with accurate depth scaling and vertex coloring.
- 📱 **Cross-Platform AR Support:** Launch AR natively on mobile devices or scan a generated QR code from desktop.
- 🗂️ **Interactive Gallery & Comparisons:** Review your project history, filter by style, and inspect transformations using an interactive before-and-after comparison slider.
- 🔐 **Secure Authentication:** Integrated email/password and Google OAuth backed by Supabase with Row-Level Security (RLS).
- 🌓 **Theme Support:** Polished light and dark modes with persistent user preferences.

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** [React 18](https://react.dev/) (Single Page Application via [Vite](https://vitejs.dev/))
- **Routing:** [React Router DOM v7](https://reactrouter.com/)
- **Styling:** CSS Custom Properties + Modern Typography + [TailwindCSS](https://tailwindcss.com/)
- **Animations:** [Framer Motion](https://www.framer.com/motion/)
- **3D & Spatial:** [Three.js](https://threejs.org/) & Google [`<model-viewer>`](https://modelviewer.dev/) (WebXR / ARCore / ARKit)
- **Icons & QR:** [Lucide React](https://lucide.dev/) & [node-qrcode](https://github.com/soldair/node-qrcode)
- **Backend SDK:** `@supabase/supabase-js`

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11) with ASGI server [Uvicorn](https://www.uvicorn.org/)
- **3D Processing:** NumPy, Trimesh, Pillow, and CPU-optimized PyTorch
- **AI Integrations:** Hugging Face Hub / Gradio Client, Replicate SDK, AI Horde
- **Containerization:** Docker (optimized for Hugging Face Spaces deployment)

### Database, Storage & Auth
- **BaaS:** [Supabase](https://supabase.com/)
- **Database:** PostgreSQL with Row-Level Security (RLS) policies
- **Storage:** Dedicated buckets for user uploads (`uploads`), generated designs (`designs`), and 3D models (`models`)
- **Authentication:** Supabase Auth (JWT-based session management)

---

## 🏗️ System Workflow

```
[ User Browser / React SPA ]
     │
     ├── 1. Upload photo & Authenticate ───────► [ Supabase (Auth + Storage + DB) ]
     │
     ├── 2. POST /generate (with Bearer JWT) ──► [ FastAPI Backend ]
     │                                                    │
     │   ◄── Returns { designId, status: processing } ────┤
     │                                                    ▼
     ├── 3. Polls status every 10s              [ Asynchronous Pipeline ]
     │                                            ├─ Line & Depth Analysis
     │                                            ├─ Conditioned AI Generation
     │                                            ├─ Download bytes from CDN
     │                                            └─ Store permanently in Supabase
     │
     └── 4. POST /generate-3d-room ────────────► [ Monocular Depth Mesh Generator ]
                                                          │
         ◄── Receives GLB URL ────────────────────────────┴─► Viewed in Three.js / WebXR AR
```

---

## 📁 Project Structure

```
ai-interior-design/
├── src/                          # React client application
│   ├── components/               # UI components (Navbar, 3D Viewers, Gallery cards, etc.)
│   ├── pages/                    # Page routes (Home, Upload, Gallery, Viewer3D, Dashboard)
│   ├── services/                 # API client, Supabase client, and Auth Context
│   ├── App.jsx                   # Router and theme providers
│   ├── main.jsx                  # Application root
│   └── index.css                 # Global styling and CSS tokens
│
├── backend/                      # Python FastAPI service
│   ├── controlnet_pipeline.py    # Geometry-aware image processing & generation
│   ├── depth_room_pipeline.py    # Monocular depth estimation & 3D GLB mesh creation
│   ├── main.py                   # REST endpoints, background tasks, CORS setup
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Container configuration for backend hosting
│
├── public/                       # Static public assets
├── supabase_setup.sql            # Core database tables and schema
├── secure_database_policies.sql  # Row-Level Security (RLS) database policies
├── secure_storage_policies.sql   # Storage bucket isolation policies
├── package.json                  # Frontend dependencies and npm scripts
└── vite.config.js                # Vite build configuration
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js:** v18.0.0 or later
- **Python:** v3.11 or later with `pip`
- **Supabase Account:** Free project on [supabase.com](https://supabase.com/)

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Akhassan12/Home-Gennie.git
cd Home-Gennie
```

---

### Step 2: Set Up Supabase

1. Create a new Supabase project.
2. In the **SQL Editor**, run the following files in order:
   - `supabase_setup.sql` (creates tables and initial triggers)
   - `secure_database_policies.sql` (enforces strict Row-Level Security on designs and profiles)
   - `secure_storage_policies.sql` (configures bucket rules for `uploads`, `designs`, and `models`)
3. Ensure the storage buckets `uploads`, `designs`, and `models` exist in the Supabase Dashboard under **Storage**.

---

### Step 3: Frontend Configuration & Installation

1. Copy the example environment file:
   ```bash
   cp .env.example .env.local
   ```
2. Open `.env.local` and add your Supabase credentials:
   ```env
   VITE_SUPABASE_URL=https://your-project-ref.supabase.co
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   VITE_API_URL=http://localhost:8000
   ```
3. Install dependencies and start the dev server:
   ```bash
   npm install
   npm run dev
   ```
   The frontend will run at `http://localhost:5173`.

---

### Step 4: Backend Configuration & Installation

1. Create and activate a Python virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   ```
   - **Windows:**
     ```powershell
     .venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(For Windows CPU PyTorch optimization, run `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu` if needed)*

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Populate `backend/.env` with your keys:
   ```env
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_KEY=your-supabase-service-role-key

   HF_TOKEN=hf_your_huggingface_token
   REPLICATE_API_TOKEN=r8_your_replicate_token
   FRONTEND_URL=http://localhost:5173
   ```

4. Start the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The API will be live at `http://localhost:8000`.

---

## ⚙️ Environment Variables Summary

### Frontend (`.env.local`)
| Variable | Description |
|---|---|
| `VITE_SUPABASE_URL` | Your Supabase project URL (`https://<ref>.supabase.co`) |
| `VITE_SUPABASE_ANON_KEY` | Public anonymous key for client-side queries |
| `VITE_API_URL` | Backend URL (`http://localhost:8000` for local dev) |

### Backend (`backend/.env`)
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Public anonymous key for baseline connectivity |
| `SUPABASE_SERVICE_KEY` | Service-role key allowing server-side uploads |
| `HF_TOKEN` | Hugging Face user access token (for inference APIs) |
| `REPLICATE_API_TOKEN` | (Optional) Replicate API token for diffusion models |
| `FRONTEND_URL` | Allowed client URL for CORS enforcement |
| `USE_FREE_MODE` | Set to `true` to prioritize free inference fallbacks |

---

## 🌐 Deployment Overview

### Frontend (Vercel)
- Connect your GitHub repository to [Vercel](https://vercel.com/).
- Set the environment variables `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL` in the project settings.
- Automatic builds run via `npm run build`.

### Backend (Hugging Face Spaces / Docker)
- Deploy using the provided `backend/Dockerfile` to Hugging Face Spaces (SDK: Docker) or any container host (Render, Fly.io, GCP).
- The container listens on port `7860` (Hugging Face default) or `8000`.
- Set container secrets corresponding to your `backend/.env` configuration.

---

## 🔒 Security

For security vulnerability reporting procedures and an overview of our security measures (such as Row-Level Security, JWT validation, and CORS restrictions), please review [SECURITY.md](SECURITY.md).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed with care by **Ali Hassan Kadri**.
