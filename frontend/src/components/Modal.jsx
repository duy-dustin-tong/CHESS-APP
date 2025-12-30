import React from 'react';

export function Modal({ children, onClose, style }) {
  return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div onClick={onClose} style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)' }} />
      <div style={{ position: 'relative', zIndex: 1001, background: 'white', padding: '16px', borderRadius: '8px', minWidth: '260px', ...style }}>
        {children}
      </div>
    </div>
  );
}

export function ConfirmDialog({ title, message, onConfirm, onCancel, confirmText = 'OK', cancelText = 'Cancel' }) {
  return (
    <div>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <div style={{ margin: '8px 0' }}>{message}</div>
      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
        <button onClick={onCancel} style={{ padding: '6px 10px' }}>{cancelText}</button>
        <button onClick={onConfirm} style={{ padding: '6px 10px', background: '#007bff', color: 'white', border: 'none' }}>{confirmText}</button>
      </div>
    </div>
  );
}

export default Modal;
