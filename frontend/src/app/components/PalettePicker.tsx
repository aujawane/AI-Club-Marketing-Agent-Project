"use client";

import { useState, useEffect } from "react";

interface PalettePickerProps {
  palette: string[];
  onChange: (palette: string[]) => void;
}

const LABELS = ["PRIMARY COLOR", "SECONDARY COLOR", "OTHER COLOR", "OTHER COLOR"];
const TEXT = "#10201a";
const MUTED = "#647067";
const BORDER = "#d8e3dd";

export default function PalettePicker({ palette, onChange }: PalettePickerProps) {
  // Use local state for inputs to allow typing partial hex codes without breaking the UI
  const [localPalette, setLocalPalette] = useState(palette);

  useEffect(() => {
    setLocalPalette(palette);
  }, [palette]);

  const handleInputChange = (index: number, value: string) => {
    let newValue = value;
    // Auto-prepend hash if missing and not empty
    if (newValue.length > 0 && !newValue.startsWith("#")) {
      newValue = "#" + newValue;
    }
    
    const newLocalPalette = [...localPalette];
    newLocalPalette[index] = newValue;
    setLocalPalette(newLocalPalette);

    // If it's a valid 7-char hex, update the parent state
    if (/^#[0-9A-Fa-f]{6}$/.test(newValue)) {
      const newPalette = [...palette];
      newPalette[index] = newValue.toUpperCase();
      onChange(newPalette);
    }
  };

  const handleColorPickerChange = (index: number, value: string) => {
    const newPalette = [...palette];
    newPalette[index] = value.toUpperCase();
    onChange(newPalette);
    
    const newLocalPalette = [...localPalette];
    newLocalPalette[index] = value.toUpperCase();
    setLocalPalette(newLocalPalette);
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "20px", marginBottom: "40px" }}>
      {localPalette.map((color, i) => (
        <div key={i} style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: "12px",
          backgroundColor: '#ffffff',
          border: `1px solid ${BORDER}`,
          borderRadius: '16px',
          padding: '20px 24px',
          transition: 'all 0.2s ease',
          boxShadow: '0 8px 22px rgba(16,32,26,0.05)',
        }}>
          <span style={{ 
            fontFamily: 'Sora, sans-serif',
            fontSize: '10px',
            fontWeight: 600,
            letterSpacing: '2px',
            textTransform: 'uppercase',
            color: MUTED,
          }}>
            {LABELS[i]}
          </span>
          
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              background: /^#[0-9A-Fa-f]{6}$/.test(color) ? color : "#000000",
              border: `2px solid ${BORDER}`,
              cursor: "pointer",
              position: "relative",
              overflow: "hidden",
              flexShrink: 0,
              boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            }}>
              <input
                type="color"
                value={/^#[0-9A-Fa-f]{6}$/.test(color) ? color : "#000000"}
                onChange={e => handleColorPickerChange(i, e.target.value)}
                style={{
                  position: "absolute",
                  inset: -10,
                  width: "200%",
                  height: "200%",
                  cursor: "pointer",
                  opacity: 0,
                }}
              />
            </div>
            
            <input
              type="text"
              value={color.toUpperCase()}
              onChange={e => handleInputChange(i, e.target.value)}
              placeholder="#FFFFFF"
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                outline: "none",
                color: TEXT,
                fontSize: "16px",
                fontFamily: "monospace",
                fontWeight: 500,
                letterSpacing: "1px",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
