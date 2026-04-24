/**
 * api.js — Frontend ↔ Backend service layer
 * All calls to the FastAPI backend go through here.
 * Base URL is read from VITE_API_URL (defaults to localhost:8000 for development).
 */

import { supabase } from './supabase'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Generic fetch wrapper with JSON handling and error extraction.
 */
async function apiFetch(path, options = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token

  const url = `${BASE_URL}${path}`
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const res = await fetch(url, { ...options, headers })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || data.message || `API error ${res.status}`)
  }
  return data
}

// ─────────────────────────────────────────────────────────────
// Health Check
// ─────────────────────────────────────────────────────────────

/**
 * Ping the backend. Returns { status: 'ok' } or throws.
 */
export async function checkHealth() {
  return apiFetch('/health')
}

// ─────────────────────────────────────────────────────────────
// AI Interior Design Generation
// ─────────────────────────────────────────────────────────────

/**
 * Send a room image URL to the backend for AI redesign.
 *
 * @param {Object} params
 * @param {string} params.userId          — Supabase user ID
 * @param {string} params.originalImageUrl — Public URL of the uploaded room photo
 * @param {string} params.style           — Design style (e.g. "Modern", "Japandi")
 * @param {string} params.roomType        — Room type (e.g. "Living Room")
 *
 * @returns {{ success: boolean, designId: string, generatedImageUrl: string }}
 */
export async function generateDesign({ userId, originalImageUrl, style, roomType }) {
  return apiFetch('/generate', {
    method: 'POST',
    body: JSON.stringify({ userId, originalImageUrl, style, roomType }),
  })
}

// ─────────────────────────────────────────────────────────────
// 3D Model Generation
// ─────────────────────────────────────────────────────────────

/**
 * Convert an image (AI-generated or original) into a 3D GLB model.
 * Uses the single-object TRELLIS pipeline (door/chair/etc reconstruction).
 *
 * @param {string} imageUrl — Public URL of the image to convert
 * @returns {{ success: boolean, glbUrl: string }}
 */
export async function generate3DModel(imageUrl, userId = '') {
  return apiFetch('/generate-3d', {
    method: 'POST',
    body: JSON.stringify({ imageUrl, userId }),
  })
}

// ─────────────────────────────────────────────────────────────────
// Full-Room 3D Reconstruction (Depth → Mesh)
// ─────────────────────────────────────────────────────────────────

/**
 * Convert a room design image into a complete 3D room mesh (GLB).
 *
 * Uses a 3-layer free depth estimation waterfall:
 *   Layer 1 → HuggingFace Inference API (free serverless)
 *   Layer 2 → HuggingFace Gradio Space  (free ZeroGPU)
 *   Layer 3 → Local CPU model           (offline fallback)
 *
 * Unlike generate3DModel(), this captures the ENTIRE room —
 * all walls, floor, ceiling, and furniture in their correct positions.
 *
 * @param {string} imageUrl — Public URL of the room image to convert
 * @param {string} userId   — Supabase user ID (for storage path)
 * @returns {{ success: boolean, glbUrl: string }}
 */
export async function generate3DRoom(imageUrl, userId = '') {
  return apiFetch('/generate-3d-room', {
    method: 'POST',
    body: JSON.stringify({ imageUrl, userId }),
  })
}
