"use client";

interface PalettePickerProps {
  palette: string[];
  onChange: (palette: string[]) => void;
}

export default function PalettePicker({ palette, onChange }: PalettePickerProps) {
  const updateColor = (index: number, newColor: string) => {
    onChange(palette.map((c, i) => i === index ? newColor : c));
  };

  return (
    <div style={{ display: "flex", gap: "34px" }}>
      {palette.map((color, i) => (
        <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
          <div style={{
            width: "120px",
            height: "120px",
            borderRadius: "12px",
            background: color,
            overflow: "hidden",
            cursor: "pointer",
            position: "relative",
            border: "1px solid rgba(0,0,0,0.1)",
          }}>
            <input
              type="color"
              value={color}
              onChange={e => updateColor(i, e.target.value)}
              style={{
                position: "absolute",
                inset: 0,
                width: "200%",
                height: "200%",
                opacity: 0,
                cursor: "pointer",
              }}
            />
          </div>
          <span style={{ fontSize: "11px", fontFamily: "monospace" }}>
            {color.toUpperCase()}
          </span>
        </div>
      ))}
    </div>
  );
}