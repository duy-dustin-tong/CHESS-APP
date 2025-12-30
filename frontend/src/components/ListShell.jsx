import React from 'react';

export default function ListShell({ title, loading, emptyMessage = 'No items.', children }) {
  return (
    <div style={{ marginTop: '20px' }}>
      {title && <h3 style={{ margin: '0 0 10px 0' }}>{title}</h3>}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div>
          {children ? children : <p>{emptyMessage}</p>}
        </div>
      )}
    </div>
  );
}
