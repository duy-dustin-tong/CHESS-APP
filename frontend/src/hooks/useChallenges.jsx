import { useState, useEffect } from 'react';
import api from '../api/api';
import socket from '../api/sockets';

export default function useChallenges(myUserId, onStart) {
  const [challenges, setChallenges] = useState([]);

  useEffect(() => {
    if (!myUserId) return;

    const fetchPending = async () => {
      try {
        const res = await api.get('/challenges/challenges/pending');
        setChallenges(res.data || []);
      } catch (err) {
        console.error('Failed to fetch pending challenges', err);
      }
    };

    fetchPending();

    const onInvite = (data) => {
      setChallenges((prev) => (prev.some((c) => c.challenge_id === data.challenge_id) ? prev : [...prev, data]));
    };

    const onStartInternal = (data) => {
      if (onStart) onStart(data);
    };

    socket.on('friend_challenge_invite', onInvite);
    socket.on('start_challenge', onStartInternal);

    return () => {
      socket.off('friend_challenge_invite', onInvite);
      socket.off('start_challenge', onStartInternal);
    };
  }, [myUserId, onStart]);

  const respondChallenge = async (challengeId, responseType) => {
    try {
      const res = await api.post(`/challenges/respond_challenge/${challengeId}/${responseType}`);
      setChallenges((prev) => prev.filter((c) => c.challenge_id !== challengeId));
      return res;
    } catch (err) {
      console.error('Failed to respond to challenge', err);
      throw err;
    }
  };

  return { challenges, respondChallenge, setChallenges };
}
