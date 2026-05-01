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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    setBannerImage(null);

    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject, grade, objectives, duration, tags, palette, tone, imageStyle, custom, title }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Generation failed");
      
      setSuccessMessage(data.message);
      if (data.image) {
        setBannerImage(data.image);
      }
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

      {successMessage && (
        <div style={{
          marginTop: '20px',
          padding: '16px',
          borderRadius: '12px',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid #10b981',
          color: '#10b981',
          textAlign: 'center',
          fontFamily: 'DM Sans, sans-serif',
        }}>
          {successMessage}
        </div>
      )}

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
              background: "#1a1f35",
              borderRadius: "24px",
              padding: "24px",
              maxWidth: "90vw",
              maxHeight: "90vh",
              display: "flex",
              flexDirection: "column",
              gap: "20px",
              alignItems: "center",
              position: "relative",
              border: "1px solid rgba(255,255,255,0.1)",
              boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
            }}
          >
            <button
              onClick={() => setBannerImage(null)}
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                background: "rgba(255,255,255,0.1)",
                border: "none",
                borderRadius: "50%",
                width: "32px",
                height: "32px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "18px",
                cursor: "pointer",
                color: "#fff",
              }}
            >
              ✕
            </button>
            <h3 style={{ 
              fontFamily: 'Sora, sans-serif', 
              color: 'white', 
              margin: 0,
              fontSize: '20px',
              fontWeight: 600 
            }}>
              Your Course Banner
            </h3>
            <img
              src={bannerImage}
              alt="Generated Banner"
              style={{ maxWidth: "100%", maxHeight: "60vh", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', alignItems: 'center' }}>
              <a
                href={bannerImage}
                download={`${title.replace(/[^a-z0-9]/gi, '_')}_banner.jpg`}
                style={{
                  width: '100%',
                  textAlign: 'center',
                  padding: "16px 0",
                  background: "linear-gradient(90deg, #7c3aed, #4f46e5)",
                  color: "#fff",
                  borderRadius: "14px",
                  textDecoration: "none",
                  fontFamily: "Sora, sans-serif",
                  fontWeight: 700,
                  fontSize: '16px',
                  boxShadow: '0 8px 20px rgba(124,58,237,0.3)',
                  transition: 'transform 0.2s',
                }}
                onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.02)'}
                onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
              >
                Download High-Res Banner
              </a>
              <button
                onClick={() => setBannerImage(null)}
                style={{
                  background: "transparent",
                  color: "rgba(255,255,255,0.5)",
                  border: "none",
                  fontFamily: "Sora, sans-serif",
                  fontSize: '14px',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
