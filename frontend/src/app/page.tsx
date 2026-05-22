"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import BannerGenerator from "./components/BannerGenerator";

const PRIMARY = "#089669";
const PRIMARY_DARK = "#067a56";
const PRIMARY_SOFT = "#ecfdf5";
const TEXT = "#10201a";
const MUTED = "#647067";
const BORDER = "#d8e3dd";
const SURFACE = "#ffffff";
const SURFACE_SOFT = "#f6faf8";

const SUBJECTS = [
  "Mathematics",
  "English Language Arts",
  "Science",
  "History & Social Studies",
  "Computer Science",
  "Creative Arts",
  "Physical Education",
  "Foreign Language",
  "Music",
  "Other",
];

const GRADE_LEVELS = [
  "Kindergarten",
  "Grade 1–3 (Early Elementary)",
  "Grade 4–5 (Upper Elementary)",
  "Grade 6–8 (Middle School)",
  "Grade 9–10 (Early High School)",
  "Grade 11–12 (Late High School)",
  "College / University",
  "Adult Learners",
];

const COLOR_PALETTES = [
  {
    id: "neutral",
    label: "Neutral",
    colors: ["#e5e5e5", "#b0b0b0", "#808080", "#404040"],
  },
  {
    id: "bold",
    label: "Bold",
    colors: ["#00c8e0", "#e040fb", "#69f442", "#ff6d00"],
  },
  {
    id: "pastel",
    label: "Pastel",
    colors: ["#b9f6ca", "#80d8ff", "#e1bee7", "#ffcdd2"],
  },
  {
    id: "ocean",
    label: "Ocean",
    colors: ["#1a237e", "#1565c0", "#42a5f5", "#ffffff"],
  },
  {
    id: "warm",
    label: "Warm",
    colors: ["#bf360c", "#e64a19", "#ff8f00", "#ffe0b2"],
  },
  {
    id: "nature",
    label: "Nature",
    colors: ["#1b5e20", "#2e7d32", "#66bb6a", "#ccff90"],
  },
];

const TONES = [
  {
    id: "professional",
    label: "Professional",
    desc: "Clear, authoritative, results driven",
    emoji: "🎯",
  },
  {
    id: "inspiring",
    label: "Inspiring",
    desc: "Motivational, visionary, energetic",
    emoji: "⭐",
  },
  {
    id: "friendly",
    label: "Friendly",
    desc: "Warm, accessible, conversational",
    emoji: "🤝",
  },
  {
    id: "academic",
    label: "Academic",
    desc: "Rigorous, detailed, scholarly",
    emoji: "🔬",
  },
  {
    id: "playful",
    label: "Playful",
    desc: "Fun, engaging, student-centered",
    emoji: "🎮",
  },
  {
    id: "creative",
    label: "Creative",
    desc: "Imaginative, exploratory, open",
    emoji: "🎨",
  },
];

const IMAGE_STYLES = [
  { id: "illustrated", label: "Illustrated", emoji: "👩‍🎨", bg: "#b9eefa" },
  { id: "photoreal", label: "Photo-real", emoji: "📸", bg: "#e2ffc9" },
  { id: "watercolor", label: "Watercolor", emoji: "🖌️", bg: "#f4cdf7" },
  { id: "geometric", label: "Geometric", emoji: "💠", bg: "#feffc9" },
];

export default function Home() {
  const [subject, setSubject] = useState("");
  const [title, setTitle] = useState("");
  const [custom, setCustom] = useState("");
  const [grade, setGrade] = useState("");
  const [objectives, setObjectives] = useState("");
  const [duration, setDuration] = useState("");
  const [palette, setPalette] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [tone, setTone] = useState("");
  const [imageStyle, setImageStyle] = useState("");
  const [uploadedJson, setUploadedJson] = useState<any>(null);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [isDraggingProjectData, setIsDraggingProjectData] = useState(false);

  const importProjectFile = (file?: File) => {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        setUploadedJson(json);
        setUploadedFileName(file.name);

        // Auto-fill basic fields for visual feedback
        if (json.title) setTitle(json.title);
        else if (json.description?.name) setTitle(json.description.name);

        if (json.tags && Array.isArray(json.tags)) setTags(json.tags);
      } catch (err) {
        console.error("Error parsing JSON:", err);
        alert("Invalid JSON file");
      }
    };
    reader.readAsText(file);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    importProjectFile(e.target.files?.[0]);
    e.target.value = "";
  };

  const swatchRef = useRef<HTMLDivElement | null>(null);
  const popoverRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const mousePos = useRef({ x: 0, y: 0 });

  const addTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && tagInput.trim()) {
      setTags([...tags, tagInput.trim()]);
      setTagInput("");
    }
  };

  const [activeEdit, setActiveEdit] = useState<{
    paletteId: string;
    colorIdx: number;
  } | null>(null);
  const [customColors, setCustomColors] = useState<
    Record<string, Record<number, string>>
  >({});

  function getSwatchColor(paletteId: string, idx: number) {
    return (
      customColors[paletteId]?.[idx] ??
      COLOR_PALETTES.find((p) => p.id === paletteId)!.colors[idx]
    );
  }

  function setSwatchColor(hex: string) {
    if (!activeEdit) return;
    const { paletteId, colorIdx } = activeEdit;
    setCustomColors((prev) => ({
      ...prev,
      [paletteId]: { ...prev[paletteId], [colorIdx]: hex },
    }));
  }

  function isOverElement(
    el: HTMLElement | null,
    x: number,
    y: number,
    padding = 0,
  ) {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    return (
      x >= r.left - padding &&
      x <= r.right + padding &&
      y >= r.top - padding &&
      y <= r.bottom + padding
    );
  }

  function startWatchingMouse() {
    if (rafRef.current) return;
    const check = () => {
      const { x, y } = mousePos.current;
      const overSwatch = isOverElement(swatchRef.current, x, y, 18);
      const overPopover = isOverElement(popoverRef.current, x, y, 18);
      if (!overSwatch && !overPopover) {
        setActiveEdit(null);
        rafRef.current = null;
      } else {
        rafRef.current = requestAnimationFrame(check);
      }
    };
    rafRef.current = requestAnimationFrame(check);
  }

  function resetSwatch() {
    if (!activeEdit) return;
    const { paletteId, colorIdx } = activeEdit;
    setCustomColors((prev) => {
      const next = { ...prev, [paletteId]: { ...prev[paletteId] } };
      delete next[paletteId][colorIdx];
      return next;
    });
  }

  useEffect(() => {
    const track = (e: MouseEvent) => {
      mousePos.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener("mousemove", track);
    return () => window.removeEventListener("mousemove", track);
  }, []);

  const steps = [
    {
      label: "PROJECT\nDETAILS",
      active: (!!subject && !!grade) || !!uploadedJson,
    },
    { label: "STYLE", active: !!palette },
    { label: "TONE", active: !!tone },
    { label: "IMAGE", active: !!imageStyle },
  ];
  const removeTag = (t: string) => setTags(tags.filter((x) => x !== t));

  const resolvedPalette = palette
    ? COLOR_PALETTES.find((p) => p.id === palette)!.colors.map((c, i) =>
        getSwatchColor(palette, i),
      )
    : [];

  const uploadedProjectTitle =
    uploadedJson?.title ||
    uploadedJson?.description?.name ||
    "Project data loaded";
  const uploadedTagCount = Array.isArray(uploadedJson?.tags)
    ? uploadedJson.tags.length
    : tags.length;

  return (
    <main
      className="min-h-screen px-6 pt-14 pb-24"
      style={{ backgroundColor: "#ffffff", color: TEXT }}
    >
      <div className="w-full max-w-[680px] mx-auto">
        {/* ── Heading ── */}
        <div>
          <br></br>
          <br></br>
        </div>
        <h1
          style={{
            margin: 0,
            fontFamily: "Sora, sans-serif",
            fontSize: "52px",
            fontWeight: 800,
            lineHeight: 0.95,
            letterSpacing: "-0.03em",
            color: TEXT,
          }}
        >
          Create your
        </h1>
        <h1
          style={{
            margin: "0 0 28px",
            fontFamily: "Sora, sans-serif",
            fontSize: "52px",
            fontWeight: 800,
            lineHeight: 1.08,
            letterSpacing: "-0.03em",
            color: PRIMARY,
          }}
        >
          Project listing
        </h1>

        <p
          style={{
            maxWidth: "520px",
            margin: "0 0 56px",
            color: MUTED,
            fontSize: "15px",
            lineHeight: 1.7,
            fontWeight: 400,
          }}
        >
          Fill in the details below, or upload a project JSON file.
          <br />
          Your unique listing will be live in under 60 seconds.
        </p>

        {/* ── Step indicator ── */}
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "flex-start",
            justifyContent: "space-between",
            width: "100%",
            marginBottom: "56px",
          }}
        >
          {steps.map((s, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <div
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  flexShrink: 0,
                  backgroundColor: s.active ? PRIMARY : "#cbd5d1",
                }}
              />
              <span
                style={{
                  fontFamily: "Sora, sans-serif",
                  fontSize: "11px",
                  fontWeight: 600,
                  letterSpacing: "1.5px",
                  textTransform: "uppercase" as const,
                  whiteSpace: "pre-line" as const,
                  color: s.active ? PRIMARY : MUTED,
                }}
              >
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {/* ── SECTION: Import JSON ── */}
        <SectionTitle>IMPORT PROJECT DATA</SectionTitle>
        <div
          style={{
            position: "relative",
            overflow: "hidden",
            borderRadius: "24px",
            border: uploadedJson
              ? `1px solid ${PRIMARY}`
              : isDraggingProjectData
                ? `1px solid ${PRIMARY}`
                : `1px solid ${BORDER}`,
            backgroundColor:
              uploadedJson || isDraggingProjectData ? PRIMARY_SOFT : SURFACE,
            boxShadow: uploadedJson
              ? "0 20px 50px rgba(8,150,105,0.14)"
              : isDraggingProjectData
                ? "0 20px 50px rgba(8,150,105,0.12)"
                : "0 14px 40px rgba(16,32,26,0.08)",
            marginBottom: "56px",
            transition: "all 0.3s ease",
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDraggingProjectData(true);
          }}
          onDragLeave={() => setIsDraggingProjectData(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDraggingProjectData(false);
            importProjectFile(e.dataTransfer.files?.[0]);
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              pointerEvents: "none",
              backgroundColor:
                uploadedJson || isDraggingProjectData
                  ? "rgba(8,150,105,0.04)"
                  : "#ffffff",
            }}
          />
          <div style={{ position: "relative", padding: "24px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "20px",
              }}
            >
              <div
                style={{
                  width: "76px",
                  height: "76px",
                  borderRadius: "18px",
                  border: `1px solid ${uploadedJson ? PRIMARY : BORDER}`,
                  backgroundColor: uploadedJson ? PRIMARY : PRIMARY_SOFT,
                  color: uploadedJson ? "#ffffff" : PRIMARY,
                  boxShadow: uploadedJson
                    ? "0 12px 28px rgba(8,150,105,0.22)"
                    : "none",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  transition: "all 0.3s ease",
                }}
              >
                {uploadedJson ? (
                  <svg
                    width="34"
                    height="34"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.9"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                ) : (
                  <svg
                    width="34"
                    height="34"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z" />
                    <path d="M14 2v5h5" />
                    <path d="M12 18v-7" />
                    <path d="m9 14 3-3 3 3" />
                  </svg>
                )}
              </div>

              <div style={{ minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    alignItems: "center",
                    gap: "8px",
                    marginBottom: "8px",
                  }}
                >
                  <span
                    style={{
                      borderRadius: "999px",
                      border: `1px solid rgba(8,150,105,0.25)`,
                      backgroundColor: PRIMARY_SOFT,
                      color: PRIMARY_DARK,
                      padding: "4px 12px",
                      fontSize: "10px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.18em",
                      fontFamily: "Sora, sans-serif",
                    }}
                  >
                    {uploadedJson ? "Ready to generate" : "JSON import"}
                  </span>
                  {uploadedFileName && (
                    <span
                      style={{
                        maxWidth: "220px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        borderRadius: "999px",
                        border: `1px solid ${BORDER}`,
                        backgroundColor: "#ffffff",
                        color: MUTED,
                        padding: "4px 12px",
                        fontSize: "11px",
                        fontWeight: 500,
                      }}
                    >
                      {uploadedFileName}
                    </span>
                  )}
                </div>

                <p
                  style={{
                    margin: "0 0 8px",
                    color: TEXT,
                    fontFamily: "Sora, sans-serif",
                    fontSize: "22px",
                    fontWeight: 700,
                    letterSpacing: "-0.01em",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {uploadedJson
                    ? uploadedProjectTitle
                    : isDraggingProjectData
                      ? "Release to import project data"
                      : "Upload project data"}
                </p>
                <p
                  style={{
                    maxWidth: "390px",
                    margin: 0,
                    color: MUTED,
                    fontSize: "14px",
                    lineHeight: "24px",
                  }}
                >
                  {uploadedJson
                    ? "Project fields were parsed and added to the form."
                    : "Drag in a project JSON file or browse from your computer."}
                </p>
              </div>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "stretch",
                  gap: "8px",
                  flexShrink: 0,
                }}
              >
                <input
                  id="project-json-upload"
                  type="file"
                  style={{ display: "none" }}
                  accept=".json,application/json"
                  onChange={handleFileUpload}
                />
                <label
                  htmlFor="project-json-upload"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    minHeight: "46px",
                    borderRadius: "14px",
                    border: `1px solid ${PRIMARY}`,
                    backgroundColor: PRIMARY,
                    color: "#ffffff",
                    padding: "0 16px",
                    fontSize: "13px",
                    fontWeight: 700,
                    fontFamily: "Sora, sans-serif",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  {uploadedJson ? "Replace file" : "Browse file"}
                </label>
                {uploadedJson && (
                  <button
                    onClick={() => {
                      setUploadedJson(null);
                      setUploadedFileName("");
                    }}
                    style={{
                      width: "46px",
                      height: "46px",
                      borderRadius: "14px",
                      border: `1px solid ${BORDER}`,
                      backgroundColor: "#ffffff",
                      color: MUTED,
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                    title="Remove file"
                    aria-label="Remove uploaded project data"
                  >
                    <span style={{ fontSize: "18px", lineHeight: 1 }}>×</span>
                  </button>
                )}
              </div>
            </div>

            {uploadedJson && (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: "8px",
                  borderTop: `1px solid ${BORDER}`,
                  paddingTop: "16px",
                  marginTop: "20px",
                }}
              >
                <div
                  style={{
                    borderRadius: "14px",
                    border: `1px solid ${BORDER}`,
                    backgroundColor: "#ffffff",
                    padding: "8px 12px",
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: "10px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.16em",
                      color: MUTED,
                    }}
                  >
                    Title
                  </p>
                  <p
                    style={{
                      margin: "4px 0 0",
                      fontSize: "13px",
                      fontWeight: 600,
                      color: TEXT,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {uploadedProjectTitle}
                  </p>
                </div>
                <div
                  style={{
                    borderRadius: "14px",
                    border: `1px solid ${BORDER}`,
                    backgroundColor: "#ffffff",
                    padding: "8px 12px",
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: "10px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.16em",
                      color: MUTED,
                    }}
                  >
                    Tags
                  </p>
                  <p
                    style={{
                      margin: "4px 0 0",
                      fontSize: "13px",
                      fontWeight: 600,
                      color: TEXT,
                    }}
                  >
                    {uploadedTagCount || 0}
                  </p>
                </div>
                <div
                  style={{
                    borderRadius: "14px",
                    border: `1px solid ${BORDER}`,
                    backgroundColor: "#ffffff",
                    padding: "8px 12px",
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: "10px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.16em",
                      color: MUTED,
                    }}
                  >
                    Status
                  </p>
                  <p
                    style={{
                      margin: "4px 0 0",
                      fontSize: "13px",
                      fontWeight: 600,
                      color: PRIMARY,
                    }}
                  >
                    Parsed
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── SECTION: Project Details ── */}
        <SectionTitle>PROJECT DETAILS</SectionTitle>

        <div className="flex flex-col gap-4 mb-12">
          <Field label="PROJECT TITLE">
            <textarea
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="   e.g. Introduction to Creative Writing"
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                outline: "none",
                color: TEXT,
                fontSize: "15px",
                fontFamily: "DM Sans, sans-serif",
                fontWeight: 300,
              }}
            />
          </Field>

          <Field label="SUBJECT">
            <div
              style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                width: "100%",
              }}
            >
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                style={{
                  width: "100%",
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: TEXT,
                  fontSize: "15px",
                  fontFamily: "DM Sans, sans-serif",
                  fontWeight: 300,
                  appearance: "none",
                  cursor: "pointer",
                  paddingRight: "24px",
                }}
              >
                <option value="" disabled>
                  Select subject
                </option>
                {SUBJECTS.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <span
                style={{
                  position: "absolute",
                  right: "0px",
                  color: MUTED,
                  pointerEvents: "none",
                  fontSize: "12px",
                }}
              >
                ▼
              </span>
            </div>
          </Field>

          <Field label="GRADE LEVEL">
            <div
              style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                width: "100%",
              }}
            >
              <select
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                style={{
                  width: "100%",
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: TEXT,
                  fontSize: "15px",
                  fontFamily: "DM Sans, sans-serif",
                  fontWeight: 300,
                  appearance: "none",
                  cursor: "pointer",
                  paddingRight: "24px",
                }}
              >
                <option value="" disabled>
                  Select grade
                </option>
                {GRADE_LEVELS.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <span
                style={{
                  position: "absolute",
                  right: "0px",
                  color: MUTED,
                  pointerEvents: "none",
                  fontSize: "12px",
                }}
              >
                ▼
              </span>
            </div>
          </Field>

          <Field label="LEARNING OBJECTIVES">
            <textarea
              value={objectives}
              onChange={(e) => setObjectives(e.target.value)}
              placeholder="What will students be able to do by the end of this project? List 2-4 outcomes"
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                outline: "none",
                color: TEXT,
                fontSize: "15px",
                fontFamily: "DM Sans, sans-serif",
                fontWeight: 300,
              }}
            />
          </Field>

          <Field label="PROJECT DURATION">
            <textarea
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              placeholder="e.g. 6 weeks, 12 hours"
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                outline: "none",
                color: TEXT,
                fontSize: "15px",
                fontFamily: "DM Sans, sans-serif",
                fontWeight: 300,
              }}
            />
          </Field>

          <Field label="KEYWORDS / TAGS">
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                gap: "10px",
              }}
            >
              {tags.map((t) => (
                <span
                  key={t}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "5px 14px",
                    borderRadius: "999px",
                    border: "1px solid rgba(8,150,105,0.3)",
                    backgroundColor: PRIMARY_SOFT,
                    color: PRIMARY,
                    fontSize: "13px",
                    fontFamily: "DM Sans, sans-serif",
                  }}
                >
                  {t}
                  {/* remove button */}
                  <button
                    onClick={() => removeTag(t)}
                    style={{
                      background: "none",
                      border: "none",
                      color: PRIMARY,
                      cursor: "pointer",
                      padding: "0",
                      fontSize: "15px",
                      lineHeight: 1,
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    ×
                  </button>
                </span>
              ))}
              {/* actual tag input  */}
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={addTag}
                placeholder="Add tag..."
                style={{
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: TEXT,
                  fontSize: "14px",
                  fontFamily: "DM Sans, sans-serif",
                  fontWeight: 300,
                  width: "100px",
                }}
              />
            </div>
          </Field>
          <Field label="CUSTOMIZATION REQUESTS (Optional)">
            <textarea
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              placeholder="Describe any specific customization requests... e.g. 'Make the title orange and add an animal in the corner'"
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                outline: "none",
                color: TEXT,
                fontSize: "15px",
                fontFamily: "DM Sans, sans-serif",
                fontWeight: 300,
              }}
            />
          </Field>
        </div>
        <br></br>
        <br></br>

        {/* ── SECTION: Style Preferences ── */}
        <SectionTitle>STYLE PREFERENCES</SectionTitle>

        {/* Color Palette */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "12px",
            marginBottom: "40px",
          }}
        >
          {COLOR_PALETTES.map((p) => (
            <button
              key={p.id}
              onClick={() => {
                setPalette(p.id);
                setActiveEdit(null);
              }}
              style={{
                position: "relative",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "16px",
                padding: "24px 16px 20px",
                borderRadius: "20px",
                border:
                  palette === p.id
                    ? `1px solid ${PRIMARY}`
                    : `1px solid ${BORDER}`,
                backgroundColor: palette === p.id ? PRIMARY_SOFT : SURFACE,
                boxShadow:
                  palette === p.id
                    ? "0 12px 30px rgba(8,150,105,0.12)"
                    : "0 8px 22px rgba(16,32,26,0.05)",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              {palette === p.id && (
                <svg
                  style={{ position: "absolute", top: "12px", right: "14px" }}
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <polyline
                    points="2,8 6,13 14,3"
                    stroke={PRIMARY}
                    strokeWidth="2"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                    fill="none"
                  />
                </svg>
              )}

              <div style={{ display: "flex" }}>
                {p.colors.map((_, i) => {
                  const color = getSwatchColor(p.id, i);
                  const isModified = color !== p.colors[i];
                  return (
                    <div
                      key={i}
                      onMouseEnter={(e) => {
                        e.stopPropagation();
                        swatchRef.current = e.currentTarget as HTMLDivElement;
                        setActiveEdit({ paletteId: p.id, colorIdx: i });
                        startWatchingMouse();
                      }}
                      style={{
                        width: "40px",
                        height: "40px",
                        borderRadius: "50%",
                        backgroundColor: color,
                        marginLeft: i === 0 ? "0" : "-16px",
                        border:
                          activeEdit?.paletteId === p.id &&
                          activeEdit?.colorIdx === i
                            ? `3px solid ${PRIMARY}`
                            : "2px solid #ffffff",
                        position: "relative",
                        zIndex:
                          activeEdit?.paletteId === p.id &&
                          activeEdit?.colorIdx === i
                            ? 10
                            : i,
                        transition: "transform 0.1s, border 0.1s",
                        transform:
                          activeEdit?.paletteId === p.id &&
                          activeEdit?.colorIdx === i
                            ? "scale(1.15)"
                            : "scale(1)",
                        outline: isModified ? `2px solid ${PRIMARY}` : "none",
                        outlineOffset: "2px",
                        cursor: "pointer",
                      }}
                    />
                  );
                })}
              </div>

              <span
                style={{
                  color: TEXT,
                  fontSize: "13px",
                  fontFamily: "DM Sans, sans-serif",
                  fontWeight: 600,
                }}
              >
                {p.label}
              </span>
            </button>
          ))}
        </div>

        {/* Portal popover — rendered at body level */}
        {activeEdit &&
          swatchRef.current &&
          createPortal(
            <div
              ref={popoverRef}
              style={{
                position: "fixed",
                top: (() => {
                  const r = swatchRef.current!.getBoundingClientRect();
                  return r.bottom + 10;
                })(),
                left: (() => {
                  const r = swatchRef.current!.getBoundingClientRect();
                  return Math.min(
                    Math.max(r.left - 70, 8),
                    window.innerWidth - 220,
                  );
                })(),
                zIndex: 9999,
                backgroundColor: SURFACE,
                border: `1px solid ${BORDER}`,
                borderRadius: "14px",
                padding: "14px",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                minWidth: "190px",
                boxShadow: "0 16px 40px rgba(16,32,26,0.14)",
              }}
            >
              <span
                style={{
                  fontSize: "10px",
                  letterSpacing: "1.5px",
                  textTransform: "uppercase" as const,
                  color: MUTED,
                  fontFamily: "Sora, sans-serif",
                }}
              >
                Adjust color
              </span>
              <div
                style={{ display: "flex", alignItems: "center", gap: "10px" }}
              >
                <input
                  type="color"
                  value={getSwatchColor(
                    activeEdit.paletteId,
                    activeEdit.colorIdx,
                  )}
                  onChange={(e) => setSwatchColor(e.target.value)}
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "50%",
                    border: "none",
                    cursor: "pointer",
                    background: "none",
                    padding: 0,
                  }}
                />
                <input
                  type="text"
                  value={getSwatchColor(
                    activeEdit.paletteId,
                    activeEdit.colorIdx,
                  )}
                  onChange={(e) => {
                    const val = e.target.value.startsWith("#")
                      ? e.target.value
                      : "#" + e.target.value;
                    if (/^#[0-9a-fA-F]{6}$/.test(val)) setSwatchColor(val);
                  }}
                  style={{
                    flex: 1,
                    background: SURFACE_SOFT,
                    border: `1px solid ${BORDER}`,
                    borderRadius: "8px",
                    padding: "6px 10px",
                    color: TEXT,
                    fontFamily: "monospace",
                    fontSize: "13px",
                    outline: "none",
                  }}
                />
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  resetSwatch();
                }}
                style={{
                  background: SURFACE_SOFT,
                  border: `1px solid ${BORDER}`,
                  borderRadius: "8px",
                  padding: "6px 10px",
                  color: MUTED,
                  fontSize: "12px",
                  cursor: "pointer",
                  fontFamily: "DM Sans, sans-serif",
                  textAlign: "left" as const,
                }}
              >
                ↺ Reset to default
              </button>
            </div>,
            document.body,
          )}
        <br></br>

        {/* Description Tone */}
        <SectionTitle>DESCRIPTION TONE</SectionTitle>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "12px",
            marginBottom: "40px",
          }}
        >
          {TONES.map((t) => (
            // selection border
            <button
              key={t.id}
              onClick={() => setTone(t.id)}
              style={{
                position: "relative",
                display: "flex",
                flexDirection: "row",
                alignItems: "flex-start",
                justifyContent: "space-between",
                padding: "24px 20px",
                borderRadius: "20px",
                border:
                  tone === t.id
                    ? `1px solid ${PRIMARY}`
                    : `1px solid ${BORDER}`,
                backgroundColor: tone === t.id ? PRIMARY_SOFT : SURFACE,
                boxShadow:
                  tone === t.id
                    ? "0 12px 30px rgba(8,150,105,0.12)"
                    : "0 8px 22px rgba(16,32,26,0.05)",
                cursor: "pointer",
                transition: "all 0.2s",
                textAlign: "left",
              }}
            >
              {/* check mark arrow  */}
              {tone === t.id && (
                <svg
                  style={{ position: "absolute", top: "12px", right: "14px" }}
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <polyline
                    points="2,8 6,13 14,3"
                    stroke={PRIMARY}
                    strokeWidth="2"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                    fill="none"
                  />
                </svg>
              )}
              {/* title */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                  paddingRight: "12px",
                }}
              >
                <span
                  style={{
                    fontFamily: "Sora, sans-serif",
                    fontSize: "16px",
                    fontWeight: 700,
                    color: TEXT,
                  }}
                >
                  {t.label}
                </span>
                {/* sub text */}
                <span
                  style={{
                    fontFamily: "DM Sans, sans-serif",
                    fontSize: "12px",
                    fontWeight: 300,
                    color: MUTED,
                    lineHeight: "1.4",
                  }}
                >
                  {t.desc}
                </span>
              </div>
              {/* emoji */}
              <span
                style={{ fontSize: "44px", flexShrink: 0, alignSelf: "center" }}
              >
                {t.emoji}
              </span>
            </button>
          ))}
        </div>
        <br></br>

        {/* Course Image Style */}

        <SectionTitle>COURSE IMAGE STYLE</SectionTitle>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "12px",
            marginBottom: "48px",
          }}
        >
          {IMAGE_STYLES.map((s) => (
            //blue border when chosen
            <button
              key={s.id}
              onClick={() => setImageStyle(s.id)}
              style={{
                position: "relative",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                borderRadius: "24px",
                border:
                  imageStyle === s.id
                    ? `1px solid ${PRIMARY}`
                    : `1px solid ${BORDER}`,
                backgroundColor: SURFACE,
                boxShadow:
                  imageStyle === s.id
                    ? "0 12px 30px rgba(8,150,105,0.12)"
                    : "0 8px 22px rgba(16,32,26,0.05)",
                cursor: "pointer",
                overflow: "hidden",
                transition: "all 0.2s",
              }}
            >
              {/* arrow sign  */}
              {imageStyle === s.id && (
                <svg
                  style={{ position: "absolute", top: "12px", right: "14px" }}
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <polyline
                    points="2,8 6,13 14,3"
                    stroke={PRIMARY}
                    strokeWidth="2"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                    fill="none"
                  />
                </svg>
              )}
              {/* background color  */}
              <div
                style={{
                  width: "110%",
                  height: "120%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "10px 0",
                  fontSize: "40px",
                  backgroundColor: s.bg,
                  borderRadius: "24px",
                  marginTop: "-1px",
                }}
              >
                {s.emoji}
              </div>
              {/* text font */}
              <div
                style={{
                  padding: "14px 0",
                  fontFamily: "Sora, sans-serif",
                  fontSize: "15px",
                  fontWeight: 600,
                  color: TEXT,
                }}
              >
                {s.label}
              </div>
            </button>
          ))}
        </div>

        {/* ── Divider ── */}
        <div
          style={{ height: "1px", backgroundColor: BORDER, margin: "50px 0" }}
        />

        {/* ── AI info box ── */}
        <div
          style={{
            backgroundColor: PRIMARY_SOFT,
            border: `1px solid ${BORDER}`,
            borderRadius: "20px",
            padding: "24px",
            marginBottom: "20px",
            display: "flex",
            alignItems: "flex-start",
            gap: "16px",
            position: "relative",
          }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "30%",
              backgroundColor: PRIMARY,
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              fontSize: "18px",
            }}
          >
            ✦
          </div>
          <p
            style={{
              fontFamily: "DM Sans, sans-serif",
              fontSize: "14px",
              color: MUTED,
              lineHeight: "1.6",
              margin: 0,
            }}
          >
            <span style={{ color: TEXT, fontWeight: 700 }}>
              The AI agent takes it from here.
            </span>{" "}
            Once you submit, your course image, polished title, and description
            will be generated simultaneously. You'll preview everything before
            anything goes live.
          </p>
        </div>
      </div>

      <BannerGenerator
        title={title}
        subject={subject}
        custom={custom}
        grade={grade}
        objectives={objectives}
        duration={duration}
        palette={resolvedPalette}
        tags={tags}
        tone={tone}
        imageStyle={imageStyle}
        uploadedJson={uploadedJson}
      />

      <br></br>
      <br></br>
      <br></br>
    </main>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "16px",
        marginBottom: "20px",
      }}
    >
      <span
        style={{
          fontFamily: "Sora, sans-serif",
          fontSize: "11px",
          fontWeight: 600,
          letterSpacing: "2px",
          textTransform: "uppercase" as const,
          color: PRIMARY,
          whiteSpace: "nowrap" as const,
        }}
      >
        {children}
      </span>
      <div style={{ flex: 1, height: "2px", backgroundColor: BORDER }} />
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        backgroundColor: SURFACE,
        border: `1px solid ${BORDER}`,
        borderRadius: "16px",
        padding: "16px 24px 20px",
        marginBottom: "12px",
        boxShadow: "0 8px 22px rgba(16,32,26,0.05)",
      }}
    >
      <label
        style={{
          display: "block",
          fontFamily: "Sora, sans-serif",
          fontSize: "10px",
          fontWeight: 600,
          letterSpacing: "2px",
          textTransform: "uppercase" as const,
          color: MUTED,
          marginBottom: "10px",
        }}
      >
        {label}
      </label>
      {children}
    </div>
  );
}
