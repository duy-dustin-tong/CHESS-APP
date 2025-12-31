// frontend/src/pages/friends-list.jsx

import { useState, useEffect, useCallback } from 'react';
import api from '../api/api';
import socket from '../api/sockets';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import StatusMessage from '../components/StatusMessage';
import UserListItem from '../components/UserListItem';
import ChallengeItem from '../components/ChallengeItem';
import useChallengeActions from '../hooks/useChallengeActions';
import ListShell from '../components/ListShell';
import usePaginatedFetch from '../hooks/usePaginatedFetch';


export default function FriendsList() {
    const [challengesState, setChallengesState] = useState([]);
    const myUserId = parseInt(localStorage.getItem('user_id'));
    const navigate = useNavigate();
    const { items: friends, loading, error, hasMore, loadMore, refresh } = usePaginatedFetch(`/users/users/${myUserId}/friends`, { pageSize: 20, params: {} });
    const [statusMessage, setStatusMessage] = useState('');
    const [waitingChallenge, setWaitingChallenge] = useState(false);


    const sendChallenge = async (friendId) => {
        try {
            setWaitingChallenge(true);
            setStatusMessage("Sending challenge...");
            await api.post('/challenges/challenges', {
                user1_id: myUserId,
                user2_id: friendId,

            });
            setStatusMessage(`Challenge sent! Waiting for response.`);
            
            // Clear message after 3 seconds
            setTimeout(() => setStatusMessage(''), 3000);
        } catch (error) {
            setStatusMessage(error.response?.data?.message || "Failed to send challenge");
            setWaitingChallenge(false);
        }
    };

    const removeFriend = async (friendId) => {
        if (!window.confirm("Are you sure you want to remove this friend?")) return;
        try {
            // This assumes your friendship delete endpoint uses the user IDs
            // Replace with your specific friendship ID logic if needed
            await api.delete(`/friendships/friendships/${friendId}`); 
            // refresh paginated list
            refresh();
        } catch (error) {
            alert(error?.response?.data?.message || "Failed to remove friend");
        }
    };

    const backToHome = () => {
        navigate('/');
    };

    const cancelChallenge = () => {
        try {
            setWaitingChallenge(false);
            setStatusMessage("Cancelling challenge...");    
            api.delete('/challenges/challenges');
            setStatusMessage("Challenge cancelled.");
        } catch (error) {
            setStatusMessage( error.response?.data?.message || "Failed to cancel challenge." );
            setWaitingChallenge(true);
        }
    };

    // use hook for challenges (keeps socket listeners centralized)
    const handleStart = useCallback((data) => navigate(`/game/${data.game_id}`), [navigate]);
    const { challenges, acceptChallenge, declineChallenge } = useChallengeActions(myUserId, handleStart);

    // keep a local alias for compatibility with existing variable names
    useEffect(() => {
      setChallengesState(challenges);
    }, [challenges]);



    // socket will join user room on connect; no need to emit register_user manually

    useEffect(() => {

        // challenge socket listeners handled by useChallenges hook
        return () => {};
    },[]);

    return (
        <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                
                <h1>My Friends</h1>
                <Button onClick={backToHome} style={{ padding: '8px 16px' }}>Back to Home</Button>
            </div>

            <hr />

                        <ListShell title="⚔️ Game Invites" emptyMessage="No game invites." loading={false}>
                            {challengesState.length > 0 && (
                                <ul style={{ listStyle: 'none', padding: 0 }}>
                                                                        {challengesState.map((c) => (
                                                                        <ChallengeItem key={c.challenge_id} challenge={c} onAccept={async (id) => { try { const res = await acceptChallenge(id); if (res?.data?.game_id) navigate(`/game/${res.data.game_id}`); } catch (err) { setStatusMessage(err.response?.data?.message || 'Failed to accept challenge'); } }} onDecline={async (id) => { try { await declineChallenge(id); } catch { setStatusMessage('Failed to decline challenge'); } }} />
                                                                    ))}
                                </ul>
                            )}
                        </ListShell>

            {loading && <p>Loading friends...</p>}
            {error && <div style={{ color: 'red' }}>{String(error)}</div>}
            {!loading && friends.length === 0 && <p>You haven't added any friends yet.</p>}
            <ul style={{ listStyle: 'none', padding: 0 }}>
                {friends.map((friend) => (
                    <UserListItem key={friend.id} user={friend} showElo actions={[{ label: 'Challenge', variant: 'plain', onClick: () => sendChallenge(friend.id) }, { label: '🗑️', variant: 'plain', onClick: () => removeFriend(friend.id) }]} />
                ))}
            </ul>
            {hasMore && <Button onClick={loadMore}>Load more</Button>}
            {waitingChallenge && 
                <Button variant="danger" onClick={cancelChallenge}>Cancel Challenge</Button>
            }
            <StatusMessage message={statusMessage} />
        </div>
    );
}