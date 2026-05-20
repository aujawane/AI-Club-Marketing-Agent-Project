"use client";

import React, { useState } from "react";

const PRIMARY = "#089669";
const PRIMARY_DARK = "#067a56";
const PRIMARY_SOFT = "#ecfdf5";
const TEXT = "#10201a";
const MUTED = "#647067";
const BORDER = "#d8e3dd";

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
  uploadedJson?: any;
}

export default function BannerGenerator({ title, subject, custom, grade, objectives, duration, palette, tags, tone, imageStyle, uploadedJson }: BannerGeneratorProps) {
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
        body: JSON.stringify({ subject, grade, objectives, duration, tags, palette, tone, imageStyle, custom, title, uploadedJson }),
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
            width: 'min(680px, calc(100vw - 48px))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            backgroundColor: loading ? PRIMARY_DARK : PRIMARY,
            border: 'none',
            borderRadius: '16px',
            padding: '22px 0',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            boxShadow: '0 14px 34px rgba(8,150,105,0.22)',
          }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.backgroundColor = PRIMARY_DARK; }}
          onMouseLeave={e => { if (!loading) e.currentTarget.style.backgroundColor = PRIMARY; }}
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
          backgroundColor: PRIMARY_SOFT,
          border: `1px solid ${PRIMARY}`,
          color: PRIMARY_DARK,
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
              background: "#ffffff",
              borderRadius: "20px",
              padding: "24px",
              maxWidth: "90vw",
              maxHeight: "90vh",
              display: "flex",
              flexDirection: "column",
              gap: "20px",
              alignItems: "center",
              position: "relative",
              border: `1px solid ${BORDER}`,
              boxShadow: "0 24px 70px rgba(16,32,26,0.2)",
            }}
          >
            <button
              onClick={() => setBannerImage(null)}
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                background: PRIMARY_SOFT,
                border: `1px solid ${BORDER}`,
                borderRadius: "50%",
                width: "32px",
                height: "32px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "18px",
                cursor: "pointer",
                color: PRIMARY,
              }}
            >
              ✕
            </button>
            <h3 style={{ 
              fontFamily: 'Sora, sans-serif', 
              color: TEXT, 
              margin: 0,
              fontSize: '20px',
              fontWeight: 600 
            }}>
              Your Course Banner
            </h3>
            <img
              src={bannerImage}
              alt="Generated Banner"
              style={{ maxWidth: "100%", maxHeight: "60vh", borderRadius: "12px", border: `1px solid ${BORDER}` }}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', alignItems: 'center' }}>
              <a
                href={bannerImage}
                download={`${title.replace(/[^a-z0-9]/gi, '_')}_banner.jpg`}
                style={{
                  width: '100%',
                  textAlign: 'center',
                  padding: "16px 0",
                  backgroundColor: PRIMARY,
                  color: "#fff",
                  borderRadius: "14px",
                  textDecoration: "none",
                  fontFamily: "Sora, sans-serif",
                  fontWeight: 700,
                  fontSize: '16px',
                  boxShadow: '0 12px 28px rgba(8,150,105,0.22)',
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
                  color: MUTED,
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
