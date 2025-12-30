import React, { useState } from 'react';
import Button from './Button';
import StatusMessage from './StatusMessage';

export default function GameControls({
  onResign,
  onOfferDraw,
  onAddFriend,
  drawOfferedBy,
  respondToDraw,
  friendRequestSent,
  myUserId,
  opponentId,
  statusMessage
}) {
  const [addFriendError, setAddFriendError] = useState('');
  return (
    <div style={{ marginBottom: '12px' }}>
      {statusMessage && <StatusMessage message={statusMessage} />}

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', margin: '8px 0' }}>
        <Button variant="danger" onClick={onResign}>Resign</Button>
        <Button onClick={onOfferDraw}>Offer Draw</Button>

        {myUserId && opponentId && !friendRequestSent && (
          <Button variant="primary" onClick={async () => {
            setAddFriendError('');
            try {
              const res = await onAddFriend();
              if (res && res.ok === false) {
                setAddFriendError(res.message || 'Failed to send friend request');
              }
            } catch (err) {
              setAddFriendError(err?.message || 'Failed to send friend request');
            }
          }}>➕ Add Friend</Button>
        )}
      </div>

      {drawOfferedBy && (
        <div style={{ background: '#fff3cd', padding: '10px', border: '1px solid #ffeeba', borderRadius: '4px', marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Opponent offered a draw.</span>
          <div>
            <Button variant="primary" onClick={() => respondToDraw(true)} style={{ marginRight: 6 }}>Accept</Button>
            <Button onClick={() => respondToDraw(false)}>Decline</Button>
          </div>
        </div>
      )}
      {addFriendError && <StatusMessage message={addFriendError} type="danger" style={{ marginTop: 8 }} />}
    </div>
  );
}
