const SAMPLE_DESIGNS = [
  {
    id: '1',
    style: 'Modern',
    palette: 'Neutral Warmth',
    imageUrl: 'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=600&h=400&fit=crop',
    score: 0.94,
  },
  {
    id: '2',
    style: 'Minimalist',
    palette: 'Cool Whites',
    imageUrl: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=600&h=400&fit=crop',
    score: 0.91,
  },
  {
    id: '3',
    style: 'Scandinavian',
    palette: 'Soft Pastels',
    imageUrl: 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=600&h=400&fit=crop',
    score: 0.89,
  },
  {
    id: '4',
    style: 'Industrial',
    palette: 'Dark Contrast',
    imageUrl: 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600&h=400&fit=crop',
    score: 0.87,
  },
  {
    id: '5',
    style: 'Bohemian',
    palette: 'Earthy Tones',
    imageUrl: 'https://images.unsplash.com/photo-1615529328331-f8917597711f?w=600&h=400&fit=crop',
    score: 0.85,
  },
  {
    id: '6',
    style: 'Classic',
    palette: 'Rich Heritage',
    imageUrl: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
    score: 0.83,
  },
]

export async function generateDesigns(roomType, style, palette, budget) {
  // Simulate AI processing delay
  await new Promise((r) => setTimeout(r, 2500))

  const filtered = style
    ? SAMPLE_DESIGNS.filter(
        (d) => d.style.toLowerCase() === style.toLowerCase()
      )
    : SAMPLE_DESIGNS

  const results = filtered.length > 0 ? filtered : SAMPLE_DESIGNS.slice(0, 4)

  return results.map((d) => ({
    ...d,
    roomType,
    generatedAt: new Date().toISOString(),
  }))
}

export function getDesignById(id) {
  return SAMPLE_DESIGNS.find((d) => d.id === id) || SAMPLE_DESIGNS[0]
}
