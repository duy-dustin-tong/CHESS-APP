import React from 'react';
import Button from './Button';

export default function ChallengeItem({ challenge, onAccept, onDecline }) {
  return (
    <li key={challenge.challenge_id} style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      marginBottom: '10px', 
      padding: '10px', 
      background: 'white',
      border: '1px solid #ddd' 
    }}>
      <span>
        <strong>{challenge.username}</strong> has challenged you to a game!
      </span>
      <div>
        <Button variant="primary" onClick={() => onAccept(challenge.challenge_id)} style={{ marginRight: 6 }}>Accept</Button>
        <Button variant="danger" onClick={() => onDecline(challenge.challenge_id)}>Decline</Button>
      </div>
    </li>
  );
}
