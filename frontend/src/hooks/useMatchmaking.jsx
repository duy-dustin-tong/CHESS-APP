import { useState } from 'react';
import api from '../api/api';

export default function useMatchmaking() {
  const [status, setStatus] = useState('');
  const [inQueue, setInQueue] = useState(false);

  const joinQueue = async () => {
    try {
      setStatus('Joining matchmaking queue...');
      const response = await api.post('/matchmaking/matchmaking');
      setStatus(response.data?.message || 'Joined');

      // If server paired immediately (returned game_id or Paired message), we're not in queue
      const paired = response.data?.message === 'Paired' || !!response.data?.game_id;
      setInQueue(!paired);

      return response;
    } catch (err) {
      setStatus(err.response?.data?.message || 'Failed to join matchmaking queue.');
      setInQueue(false);
      throw err;
    }
  };

  const leaveQueue = async () => {
    try {
      setStatus('Leaving matchmaking queue...');
      const response = await api.delete('/matchmaking/matchmaking');
      setStatus(response.data?.message || 'Left');
      setInQueue(false);
      return response;
    } catch (err) {
      setStatus(err.response?.data?.message || 'Failed to leave matchmaking queue.');
      throw err;
    }
  };

  return { status, inQueue, joinQueue, leaveQueue, setStatus, setInQueue };
}
