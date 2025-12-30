import React from 'react';

export default function Button({ children, variant = 'primary', onClick, style, title, type = 'button' }) {
  const base = {
    padding: '8px 12px',
    borderRadius: '6px',
    cursor: 'pointer',
    border: 'none',
    fontWeight: 600
  };

  const variants = {
    primary: { backgroundColor: '#007bff', color: 'white' },
    danger: { backgroundColor: '#dc3545', color: 'white' },
    plain: { background: 'none', color: 'inherit', border: '1px solid transparent' }
  };

  return (
    <button type={type} title={title} onClick={onClick} style={{ ...base, ...(variants[variant] || variants.primary), ...style }}>
      {children}
    </button>
  );
}
