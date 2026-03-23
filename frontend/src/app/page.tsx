'use client'

import { useState } from 'react'

const SUBJECTS = [
  'Mathematics', 'English Language Arts', 'Science',
  'History & Social Studies', 'Computer Science', 'Creative Arts',
  'Physical Education', 'Foreign Language', 'Music', 'Other',
]

const GRADE_LEVELS = [
  'Kindergarten', 'Grade 1–3 (Early Elementary)', 'Grade 4–5 (Upper Elementary)',
  'Grade 6–8 (Middle School)', 'Grade 9–10 (Early High School)',
  'Grade 11–12 (Late High School)', 'College / University', 'Adult Learners',
]

const COLOR_PALETTES = [
  { id: 'neutral', label: 'Neutral', colors: ['#e5e5e5', '#b0b0b0', '#808080', '#404040'] },
  { id: 'bold',    label: 'Bold',    colors: ['#00c8e0', '#e040fb', '#69f442', '#ff6d00'] },
  { id: 'pastel',  label: 'Pastel',  colors: ['#b9f6ca', '#80d8ff', '#e1bee7', '#ffcdd2'] },
  { id: 'ocean',   label: 'Ocean',   colors: ['#1a237e', '#1565c0', '#42a5f5', '#ffffff'] },
  { id: 'warm',    label: 'Warm',    colors: ['#bf360c', '#e64a19', '#ff8f00', '#ffe0b2'] },
  { id: 'nature',  label: 'Nature',  colors: ['#1b5e20', '#2e7d32', '#66bb6a', '#ccff90'] },
]

const TONES = [
  { id: 'professional', label: 'Professional', desc: 'Clear, authoritative, results driven', emoji: '🎯' },
  { id: 'inspiring',    label: 'Inspiring',    desc: 'Motivational, visionary, energetic',  emoji: '⭐' },
  { id: 'friendly',     label: 'Friendly',     desc: 'Warm, accessible, conversational',    emoji: '🤝' },
  { id: 'academic',     label: 'Academic',     desc: 'Rigorous, detailed, scholarly',       emoji: '🔬' },
  { id: 'playful',      label: 'Playful',      desc: 'Fun, engaging, student-centered',     emoji: '🎮' },
  { id: 'creative',     label: 'Creative',     desc: 'Imaginative, exploratory, open',      emoji: '🎨' },
]

const IMAGE_STYLES = [
  { id: 'illustrated', label: 'Illustrated', emoji: '👩‍🎨', bg: '#b9eefa' },
  { id: 'photoreal',   label: 'Photo-real',  emoji: '📸',   bg: '#e2ffc9' },
  { id: 'watercolor',  label: 'Watercolor',  emoji: '🖌️',   bg: '#f4cdf7' },
  { id: 'geometric',   label: 'Geometric',   emoji: '💠',   bg: '#feffc9' },
]



export default function Home() {
  const [subject, setSubject]       = useState('')
  const [title, setTitle]       = useState('')
  const [grade, setGrade]           = useState('')
  const [objectives, setObjectives] = useState('')
  const [duration, setDuration]     = useState('')
  const [tags, setTags]             = useState<string[]>([])
  const [tagInput, setTagInput]     = useState('')
  const [palette, setPalette]       = useState('')
  const [tone, setTone]             = useState('')
  const [imageStyle, setImageStyle] = useState('')

  const addTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      setTags([...tags, tagInput.trim()])
      setTagInput('')
    }
  }

//   const steps = [
//   { label: 'COURSE\nDETAILS', active: true },
//   { label: 'STYLE',           active: false },
//   { label: 'PREVIEW',         active: false },
//   { label: 'PUBLISH',         active: false },
// ]

const steps = [
  { label: 'COURSE\nDETAILS', active: !!subject && !!grade },
  { label: 'STYLE',           active: !!palette },
  { label: 'TONE',            active: !!tone },
  { label: 'IMAGE',           active: !!imageStyle },
]
  const removeTag = (t: string) => setTags(tags.filter(x => x !== t))

  return (
    <main className="min-h-screen bg-[#0d1129] px-6 pt-14 pb-24">
      <div className="w-full max-w-[600px] mx-auto">

        {/* ── Heading ── */}
        <div><br></br><br></br></div>
        <h1 className="text-[52px] font-extrabold leading-[0.02] tracking-tight text-white"
          style={{ fontFamily: 'Sora, sans-serif' }}>
          Create your
        </h1>
        <h1 className="text-[52px] font-extrabold leading-[1] tracking-tight italic gradient-text mb-8"
          style={{ fontFamily: 'Sora, sans-serif' }}>
          course listing
        </h1>

        <p className="text-[15px] leading-[1.7] text-white/40 font-light mb-14 max-w-[480px]">
          Fill in the details below, and our AI agent handles the rest.
          <br />Your unique listing will be live in under 60 seconds.
          
        </p>
        <br></br>
        <br></br>
        {/* ── Step indicator ── */}
       <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', width: '100%', marginBottom: '56px' }}>
          {steps.map((s, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                flexShrink: 0,
                backgroundColor: s.active ? '#8b5cf6' : '#6b7280',
              }} />
              <span style={{
                fontFamily: 'Sora, sans-serif',
                fontSize: '11px',
                fontWeight: 600,
                letterSpacing: '1.5px',
                textTransform: 'uppercase' as const,
                whiteSpace: 'pre-line' as const,
                color: s.active ? '#a78bfa' : '#9ca3af',
              }}>
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {/* ── SECTION: Course Details ── */}    
        <SectionTitle>COURSE DETAILS</SectionTitle>

        <div className="flex flex-col gap-4 mb-12">

          <Field label="COURSE TITLE">
            <textarea
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="   e.g. Introduction to Creative Writing"
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#9ca3af',
                fontSize: '15px',
                fontFamily: 'DM Sans, sans-serif',
                fontWeight: 300,
              }} />
          </Field>

          <Field label="SUBJECT">
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%' }}>
                <select
                  value={subject}
                  onChange={e => setSubject(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    color: '#FFFFFF',
                    fontSize: '15px',
                    fontFamily: 'DM Sans, sans-serif',
                    fontWeight: 300,
                    appearance: 'none',
                    cursor: 'pointer',
                    paddingRight: '24px',
                  }}
                >
                  <option value="" disabled>Select subject</option>
                  {SUBJECTS.map(s => <option key={s}>{s}</option>)}
                </select>
                <span style={{ position: 'absolute', right: '0px', color: '#9ca3af', pointerEvents: 'none', fontSize: '12px' }}>▼</span>
              </div>
          </Field>

          <Field label="GRADE LEVEL">
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%' }}>
                <select
                  value={grade}
                  onChange={e => setGrade(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    color: '#FFFFFF',
                    fontSize: '15px',
                    fontFamily: 'DM Sans, sans-serif',
                    fontWeight: 300,
                    appearance: 'none',
                    cursor: 'pointer',
                    paddingRight: '24px',
                  }}
                >
                  <option value="" disabled>Select grade</option>
                  {GRADE_LEVELS.map(s => <option key={s}>{s}</option>)}
                </select>
                <span style={{ position: 'absolute', right: '0px', color: '#9ca3af', pointerEvents: 'none', fontSize: '12px' }}>▼</span>
              </div>
          </Field>

        <Field label="LEARNING OBJECTIVES">
            <textarea
              value={objectives}
              onChange={e => setObjectives(e.target.value)}
              placeholder="What will students be able to do by the end of this course? List 2-4 outcomes"
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#9ca3af',
                fontSize: '15px',
                fontFamily: 'DM Sans, sans-serif',
                fontWeight: 300,
              }} />
          </Field>

          <Field label="COURSE DURATION">
            <textarea
              value={duration}
              onChange={e => setDuration(e.target.value)}
              placeholder="e.g. 6 weeks, 12 hours"
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#9ca3af',
                fontSize: '15px',
                fontFamily: 'DM Sans, sans-serif',
                fontWeight: 300,
              }} /></Field>

          <Field label="KEYWORDS / TAGS">
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
            {tags.map(t => (
              <span key={t} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '5px 14px',
                borderRadius: '999px',
                border: '1px solid rgba(139,92,246,0.5)',
                backgroundColor: 'rgba(139,92,246,0.12)',
                color: '#a78bfa',
                fontSize: '13px',
                fontFamily: 'DM Sans, sans-serif',
              }}>
                {t}
                {/* remove button */}
                <button
                  onClick={() => removeTag(t)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#a78bfa',
                    cursor: 'pointer',
                    padding: '0',
                    fontSize: '15px',
                    lineHeight: 1,
                    display: 'flex',
                    alignItems: 'center',
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
              onChange={e => setTagInput(e.target.value)}
              onKeyDown={addTag}
              placeholder="Add tag..."
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#9ca3af',
                fontSize: '14px',
                fontFamily: 'DM Sans, sans-serif',
                fontWeight: 300,
                width: '100px',
              }}
            />
          </div>
          </Field>
        </div>
        <br></br>
        <br></br>

        {/* ── SECTION: Style Preferences ── */}
        <SectionTitle>STYLE PREFERENCES</SectionTitle>

        {/* Color Palette */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '40px' }}>
        {COLOR_PALETTES.map(p => (
          <button
            key={p.id}
            onClick={() => setPalette(p.id)}
            style={{
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '16px',
              padding: '24px 16px 20px',
              borderRadius: '20px',
              border: palette === p.id ? '1px solid #8b5cf6' : '1px solid rgba(255,255,255,0.07)',
              backgroundColor: palette === p.id ? '#1c1f3a' : '#1a1f35',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {/* arrow in corner */}
            {palette === p.id && (
              <svg
                  style={{ position: 'absolute', top: '12px', right: '14px' }}
                  width="16" height="16" viewBox="0 0 16 16" fill="none"
                >
                  <polyline
                    points="2,8 6,13 14,3"
                    stroke="#a78bfa"
                    strokeWidth="2"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                    fill="none"
                  />
                </svg>)}
                {/* colored circles */}
            <div style={{ display: 'flex'}}>
              {p.colors.map((c, i) => (
                <div key={i} style={{ 
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: c,
                  marginLeft: i === 0 ? '0' : '-16px',
                  border: '2px solid #1a1f35',
                }} />
              ))}
            </div>
            {/* title */}
            <span style={{
              color: '#9ca3af',
              fontSize: '13px',
              fontFamily: 'DM Sans, sans-serif',
            }}>
              {p.label}
            </span>
          </button>
        ))}
      </div>
      <br></br>

        {/* Description Tone */}
        <SectionTitle>DESCRIPTION TONE</SectionTitle>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '40px' }}>
          {TONES.map(t => (
            // selection border 
            <button
              key={t.id}
              onClick={() => setTone(t.id)}
              style={{
                position: 'relative',
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                padding: '24px 20px',
                borderRadius: '20px',
                border: tone === t.id ? '1px solid #07bdfa' : '1px solid rgba(255,255,255,0.07)',
                backgroundColor: tone === t.id ? '#0a1f2e' : '#1a1f35',
                cursor: 'pointer',
                transition: 'all 0.2s',
                textAlign: 'left',
              }}
            >
              {/* check mark arrow  */}
              {tone === t.id && (
                <svg
                  style={{ position: 'absolute', top: '12px', right: '14px' }}
                  width="16" height="16" viewBox="0 0 16 16" fill="none"
                >
                  <polyline
                    points="2,8 6,13 14,3"
                    stroke="#07bdfa"
                    strokeWidth="2"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                    fill="none"
                  />
                </svg>
              )}
              {/* title */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '12px' }}>
                <span style={{
                  fontFamily: 'Sora, sans-serif',
                  fontSize: '16px',
                  fontWeight: 700,
                  color: '#ffffff',
                }}>
                  {t.label}
                </span>
                {/* sub text */}
                <span style={{
                  fontFamily: 'DM Sans, sans-serif',
                  fontSize: '12px',
                  fontWeight: 300,
                  color: '#6b7280',
                  lineHeight: '1.4',
                }}>
                  {t.desc}
                </span>
              </div>
              {/* emoji */}
              <span style={{ fontSize: '44px', flexShrink: 0, alignSelf: 'center' }}>{t.emoji}</span>
            </button>
          ))}
        </div>
        <br></br>

        {/* Course Image Style */}

         <SectionTitle>COURSE IMAGE STYLE</SectionTitle>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '48px' }}>
          {IMAGE_STYLES.map(s => (
            //blue border when chosen 
            <button
              key={s.id}
              onClick={() => setImageStyle(s.id)}
              style={{
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                borderRadius: '24px',
                border: imageStyle === s.id ? '1px solid #07bdfa' : '1px solid rgba(255,255,255,0.07)',
                backgroundColor: '#1a1f35',
                cursor: 'pointer',
                overflow: 'hidden',
                transition: 'all 0.2s',
              }}
            >
              {/* arrow sign  */}
              {imageStyle === s.id && (
                <svg
                  style={{ position: 'absolute', top: '12px', right: '14px' }}
                  width="16" height="16" viewBox="0 0 16 16" fill="none"
                >
                  <polyline
                    points="2,8 6,13 14,3"
                    stroke="#07bdfa"
                    strokeWidth="2"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                    fill="none"
                  />
                </svg>
              )}
              {/* background color  */}
              <div style={{
                width: '110%',
                height: '120%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '10px 0',
                fontSize: '40px',
                backgroundColor: s.bg,
                borderRadius: '24px',
                marginTop: '-1px',
              }}>
                {s.emoji}
              </div>
              {/* text font */}
              <div style={{
                padding: '14px 0',
                fontFamily: 'Sora, sans-serif',
                fontSize: '15px',
                fontWeight: 600,
                color: '#ffffff',
              }}>
                {s.label}
              </div>
            </button>
          ))}
        </div>

        {/* ── Divider ── */}
        <div style={{ height: '1px', backgroundColor: '#7d7c7c', margin: '50px 0'}} />

        {/* ── AI info box ── */}
        <div style={{
          backgroundColor: '#1a1f35',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '20px',
          padding: '24px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '16px',
          position: 'relative',
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '30%',
            backgroundColor: '#1e1040',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            fontSize: '18px',
          }}>
            ✦
          </div>
          <p style={{
            fontFamily: 'DM Sans, sans-serif',
            fontSize: '14px',
            color: 'rgba(255,255,255,0.7)',
            lineHeight: '1.6',
            margin: 0,
          }}>
            <span style={{ color: '#ffffff', fontWeight: 700 }}>The AI agent takes it from here.</span>{' '}
            Once you submit, your course image, polished title, and description will be generated
            simultaneously. You'll preview everything before anything goes live.
          </p>
          
        </div>

        {/* ── Generate button ── */}
       <button
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          backgroundColor: '#7c3aed',
          border: 'none',
          borderRadius: '20px',
          padding: '22px 0',
          cursor: 'pointer',
          transition: 'all 0.2s',
          boxShadow: '0 4px 32px rgba(124,58,237,0.4)',
        }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#6d28d9')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#7c3aed')}
      >
        <span style={{ fontSize: '20px', color: 'white' }}>✦</span>
        <span style={{
          fontFamily: 'Sora, sans-serif',
          fontSize: '18px',
          fontWeight: 700,
          color: 'white',
          letterSpacing: '0.3px',
        }}>
          Generate My Course Listing
        </span>
      </button>
      <div style={{ height: '150px' }} />

      </div>
    </main>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
      <span style={{
        fontFamily: 'Sora, sans-serif',
        fontSize: '11px',
        fontWeight: 600,
        letterSpacing: '2px',
        textTransform: 'uppercase' as const,
        color: '#9ca3af',
        whiteSpace: 'nowrap' as const,
      }}>
        {children}
      </span>
      <div style={{ flex: 1, height: '2px', backgroundColor: 'rgba(255,255,255,0.08)' }} />
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{
      backgroundColor: '#1a1f35',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '16px',
      padding: '16px 24px 20px',
      marginBottom: '12px',
    }}>
      <label style={{
        display: 'block',
        fontFamily: 'Sora, sans-serif',
        fontSize: '10px',
        fontWeight: 600,
        letterSpacing: '2px',
        textTransform: 'uppercase' as const,
        color: '#6b7280',
        marginBottom: '10px',
      }}>
        {label}
      </label>
      {children}
    </div>
  )
}