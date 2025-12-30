import React from 'react';

export default function StatusMessage({ message, type = 'info', style }) {
  if (!message) return null;
  const base = {
    padding: '8px 12px',
    borderRadius: '6px',
    marginTop: '10px'
  };

  const colors = {
    info: { background: '#e7f3ff', color: '#034ea2', border: '1px solid #cfe6ff' },
    success: { background: '#e6ffef', color: '#0b6623', border: '1px solid #bff1c9' },
    danger: { background: '#fff0f0', color: '#8a1f1f', border: '1px solid #ffd6d6' }
  };

  return (
    <div style={{ ...base, ...(colors[type] || colors.info), ...style }}>
      {message}
    </div>
  );
}
