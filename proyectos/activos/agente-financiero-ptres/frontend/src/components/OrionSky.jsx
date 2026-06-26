const ORION = [
  { x: 500, y: 70,  r: 3.0, c: "#fff4dd", g: 9  },
  { x: 360, y: 235, r: 6.0, c: "#ffb27a", g: 22 },
  { x: 650, y: 195, r: 4.4, c: "#eaf2ff", g: 15 },
  { x: 430, y: 360, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 505, y: 388, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 580, y: 412, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 320, y: 560, r: 6.0, c: "#cfe2ff", g: 22 },
  { x: 690, y: 540, r: 4.4, c: "#dbe7ff", g: 15 },
  { x: 780, y: 120, r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 850, y: 55,  r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 235, y: 205, r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 215, y: 100, r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 240, y: 345, r: 2.6, c: "#ffe9c2", g: 8  },
]

const _seed = (() => { let s = 1723; return () => (s = (s * 9301 + 49297) % 233280) / 233280 })()
const FAR  = Array.from({ length: 70 }, () => ({ x: _seed()*1000, y: _seed()*620, r: _seed()*0.8+0.3,  o: _seed()*0.35+0.1,  d: _seed()*6 }))
const NEAR = Array.from({ length: 30 }, () => ({ x: _seed()*1000, y: _seed()*620, r: _seed()*1.2+0.7, o: _seed()*0.5+0.45, d: _seed()*5 }))

export default function OrionSky() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      <style>{`
        @keyframes orionTwinkle { 0%,100%{opacity:.15} 50%{opacity:.7} }
        @keyframes orionPulse   { 0%,100%{opacity:.55} 50%{opacity:1} }
        @keyframes nebDrift     { 0%,100%{opacity:.55} 50%{opacity:.95} }
      `}</style>
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1000 620" preserveAspectRatio="xMidYMid slice" fill="none" aria-hidden="true">
        <defs>
          <radialGradient id="spaceGlow" cx="46%" cy="40%" r="75%">
            <stop offset="0%"   stopColor="#1d3050" />
            <stop offset="42%"  stopColor="#101f36" />
            <stop offset="100%" stopColor="#060c18" />
          </radialGradient>
          <radialGradient id="nebA" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#f59e0b" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="nebB" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#3b6fd4" stopOpacity="0.26" />
            <stop offset="100%" stopColor="#3b6fd4" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%"   stopColor="#ffd79b" stopOpacity="0.0" />
            <stop offset="50%"  stopColor="#ffce8a" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#ffd79b" stopOpacity="0.0" />
          </linearGradient>
          <filter id="soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.2" /></filter>
          <filter id="glow" x="-400%" y="-400%" width="900%" height="900%">
            <feGaussianBlur stdDeviation="6" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <rect width="1000" height="620" fill="url(#spaceGlow)" />
        <g style={{ animation: "nebDrift 9s ease-in-out infinite" }}>
          <ellipse cx="430" cy="380" rx="340" ry="250" fill="url(#nebA)" />
        </g>
        <g style={{ animation: "nebDrift 11s ease-in-out 1.5s infinite" }}>
          <ellipse cx="700" cy="170" rx="280" ry="210" fill="url(#nebB)" />
          <ellipse cx="240" cy="520" rx="240" ry="190" fill="url(#nebB)" />
        </g>
        <g fill="#9fb4d6" filter="url(#soft)">
          {FAR.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.r} opacity={s.o}
              style={{ animation: `orionTwinkle ${4+s.d}s ease-in-out ${s.d}s infinite` }} />
          ))}
        </g>
        <g fill="#ffffff">
          {NEAR.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.r} opacity={s.o}
              style={{ animation: `orionTwinkle ${3+s.d}s ease-in-out ${s.d}s infinite` }} />
          ))}
        </g>
        <g fill="none" strokeLinecap="round" strokeLinejoin="round">
          <g stroke="#ffce8a" strokeWidth="3" opacity="0.18" filter="url(#soft)">
            <polyline points="500,70 360,235 650,195 500,70" />
            <polyline points="360,235 430,360 505,388 580,412 650,195" />
            <line x1="430" y1="360" x2="320" y2="560" />
            <line x1="580" y1="412" x2="690" y2="540" />
            <polyline points="650,195 780,120 850,55" />
            <polyline points="360,235 235,205 215,100" />
            <line x1="235" y1="205" x2="240" y2="345" />
          </g>
          <g stroke="url(#lineGrad)" strokeWidth="1.1" opacity="0.65">
            <polyline points="500,70 360,235 650,195 500,70" />
            <polyline points="360,235 430,360 505,388 580,412 650,195" />
            <line x1="430" y1="360" x2="320" y2="560" />
            <line x1="580" y1="412" x2="690" y2="540" />
            <polyline points="650,195 780,120 850,55" />
            <polyline points="360,235 235,205 215,100" />
            <line x1="235" y1="205" x2="240" y2="345" />
          </g>
        </g>
        <g filter="url(#soft)">
          {ORION.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.g} fill={s.c} opacity="0.16"
              style={{ animation: `orionPulse ${5+(i%4)}s ease-in-out ${i*0.4}s infinite` }} />
          ))}
        </g>
        <g filter="url(#glow)">
          {ORION.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.r} fill={s.c}
              style={{ animation: `orionPulse ${4+(i%3)}s ease-in-out ${i*0.3}s infinite` }} />
          ))}
        </g>
      </svg>
    </div>
  )
}
