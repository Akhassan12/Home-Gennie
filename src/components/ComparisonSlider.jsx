import { useState } from 'react'

export default function ComparisonSlider({ before, after }) {
  const [sliderPos, setSliderPos] = useState(50)

  const handleSliderChange = (e) => {
    setSliderPos(e.target.value)
  }

  return (
    <div className="relative w-full aspect-[4/3] rounded-xl overflow-hidden cursor-ew-resize select-none border border-white/10 group">
      {/* After Image (Base) */}
      <img
        src={after}
        alt="After"
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Before Image (Top) */}
      <div
        className="absolute inset-0 w-full h-full"
        style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
      >
        <img
          src={before}
          alt="Before"
          className="w-full h-full object-cover"
        />
        {/* Label Before */}
        <div className="absolute top-4 left-4 px-2 py-1 bg-black/50 backdrop-blur rounded text-[10px] text-white font-bold tracking-widest uppercase">
          Original
        </div>
      </div>

      {/* Label After */}
      <div className="absolute top-4 right-4 px-2 py-1 bg-primary-600/70 backdrop-blur rounded text-[10px] text-white font-bold tracking-widest uppercase">
        AI Design
      </div>

      {/* Slider Line */}
      <div
        className="absolute inset-y-0 w-0.5 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)] z-10"
        style={{ left: `${sliderPos}%` }}
      >
        {/* Slider Handle */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow-xl flex items-center justify-center pointer-events-none">
          <div className="w-1 h-3 bg-surface-800 rounded-full mx-0.5" />
          <div className="w-1 h-3 bg-surface-800 rounded-full mx-0.5" />
        </div>
      </div>

      {/* Input Overlay */}
      <input
        type="range"
        min="0"
        max="100"
        value={sliderPos}
        onChange={handleSliderChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
      />
    </div>
  )
}
