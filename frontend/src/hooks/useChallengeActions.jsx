import useChallenges from './useChallenges';
import useMatchmaking from './useMatchmaking';
import { useCallback } from 'react';

export default function useChallengeActions(myUserId, onStart) {
  const { challenges, respondChallenge, setChallenges } = useChallenges(myUserId, onStart);
  const { leaveQueue, inQueue } = useMatchmaking();

  const acceptChallenge = useCallback(async (challengeId) => {
    const res = await respondChallenge(challengeId, 'accept');
    try {
      if (inQueue) await leaveQueue();
    } catch (e) {
      // ignore errors leaving queue (not critical)
    }
    return res;
  }, [respondChallenge, leaveQueue, inQueue]);

  const declineChallenge = useCallback(async (challengeId) => {
    return await respondChallenge(challengeId, 'decline');
  }, [respondChallenge]);

  return { challenges, acceptChallenge, declineChallenge, setChallenges };
}
