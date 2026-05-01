"use client";

import React, { useState } from "react";

interface BannerGeneratorProps {
  title: string;
  subject: string;
  custom: string;
  grade: string;
  objectives: string;
  duration: string;
  palette: string[];
  tags: string[];
  tone: string;
  imageStyle: string;
}

export default function BannerGenerator({ title, subject, custom, grade, objectives, duration, palette, tags, tone, imageStyle }: BannerGeneratorProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [bannerImage, setBannerImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject, grade, objectives, duration, tags, palette, tone, imageStyle, custom, title }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Generation failed");
      setBannerImage(data.image);
    } catch (err: any) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div style={{ display: "flex", justifyContent: "center", width: "100%" }}>
        <button
          onClick={handleGenerate}
          disabled={loading}
          style={{
            width: '600px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            backgroundColor: loading ? '#4c1d95' : '#7c3aed',
            border: 'none',
            borderRadius: '20px',
            padding: '22px 0',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            boxShadow: '0 4px 32px rgba(124,58,237,0.4)',
          }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.backgroundColor = '#6d28d9'; }}
          onMouseLeave={e => { if (!loading) e.currentTarget.style.backgroundColor = '#7c3aed'; }}
        >
          <span style={{ fontSize: '20px', color: 'white' }}>✦</span>
          <span style={{
            fontFamily: 'Sora, sans-serif',
            fontSize: '18px',
            fontWeight: 700,
            color: 'white',
            letterSpacing: '0.3px',
          }}>
            {loading ? 'Generating...' : 'Generate My Course Listing'}
          </span>
        </button>
      </div>

      {error && (
        <div style={{
          marginTop: '20px',
          padding: '16px',
          borderRadius: '12px',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid #ef4444',
          color: '#ef4444',
          textAlign: 'center',
          fontFamily: 'DM Sans, sans-serif',
        }}>
          {error}
        </div>
      )}

      {/* Modal */}
      {bannerImage && (
        <div
          onClick={() => setBannerImage(null)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.75)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}
            style={{
              background: "#fff",
              borderRadius: "12px",
              padding: "24px",
              maxWidth: "90vw",
              maxHeight: "90vh",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              alignItems: "center",
              position: "relative",
            }}
          >
            <button
              onClick={() => setBannerImage(null)}
              style={{
                position: "absolute",
                top: "-14px",
                left: "-14px",
                background: "#fff",
                border: "2px solid #888",
                borderRadius: "50%",
                width: "28px",
                height: "28px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "14px",
                cursor: "pointer",
                color: "#888",
                lineHeight: 1,
              }}
            >
              ✕
            </button>
            <img
              src={bannerImage}
              alt="Generated Banner"
              style={{ maxWidth: "100%", maxHeight: "70vh", borderRadius: "8px" }}
            />
            <a
            
              href={bannerImage}
              download="banner.jpg"
              style={{
                padding: "10px 20px",
                background: "#7c3aed",
                color: "#fff",
                borderRadius: "8px",
                textDecoration: "none",
                fontFamily: "Sora, sans-serif",
                fontWeight: 600,
              }}
            >
              Download
            </a>
          </div>
        </div>
      )}
    </>
  );
}