import React from 'react';
import Button from './Button';

export default function UserListItem({ user, showElo = false, actions = [] }) {
  return (
    <li style={{ marginBottom: '10px', padding: '10px', border: '1px solid #eee', borderRadius: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <strong style={{ display: 'block' }}>{user.username}</strong>
        {showElo && <div style={{ color: '#666' }}>Elo: {user.elo}</div>}
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        {actions.map((a, i) => (
          <Button key={i} variant={a.variant || 'plain'} onClick={a.onClick} title={a.title} style={a.style}>
            {a.label}
          </Button>
        ))}
      </div>
    </li>
  );
}
