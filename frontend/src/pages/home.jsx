// frontend/src/pages/home.jsx
import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import socket from '../api/sockets';
import StatusMessage from '../components/StatusMessage';
import Button from '../components/Button';
import ChallengeItem from '../components/ChallengeItem';
import UserListItem from '../components/UserListItem';
import useFriendRequests from '../hooks/useFriendRequests';
import useChallengeActions from '../hooks/useChallengeActions';
import useMatchmaking from '../hooks/useMatchmaking';
import ListShell from '../components/ListShell';



export default function Home() {
    const navigate = useNavigate();

    const [username, setUsername] = useState(null);
    const [message, setMessage] = useState('');
    const [myUserId, setMyUserId] = useState(parseInt(localStorage.getItem('user_id')));
    const { friendRequests, acceptRequest, declineRequest, message: frMessage, setMessage: setFrMessage } = useFriendRequests(myUserId);
    const handleStart = useCallback((data) => navigate(`/game/${data.game_id}`), [navigate]);
    const { challenges, acceptChallenge, declineChallenge } = useChallengeActions(myUserId, handleStart);
    const { joinQueue } = useMatchmaking();



    


    // respondChallenge comes from useChallenges


    // 2. ACCEPT REQUEST (PUT)
    // acceptRequest/declineRequest come from useFriendRequests

    const handleLogout = () => {


        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('username');
        localStorage.removeItem('user_id');
        
        setMessage("Logged out successfully.");
        setUsername(null);

        // Disconnect socket on logout so server removes the connection from rooms
        try { socket.disconnect(); } catch (e) { /* ignore */ }
    };

    const seeFriends = () => {
        navigate('/friends-list');
    }

    const handleJoinQueue = async () => {
        try {
            setMessage('Joining matchmaking queue...');
            const response = await joinQueue();
            if (response?.data?.message === 'Paired' || response?.data?.game_id) {
                navigate(`/game/${response.data.game_id}`);
                return;
            }
            setMessage(response.data?.message || 'Waiting');
            navigate('/waiting-room');
        } catch (err) {
            setMessage(err.response?.data?.message || 'Failed to join matchmaking queue.');
        }
    };
    


    useEffect(() => {
        const storedUsername = localStorage.getItem('username');
        if (storedUsername) {
            setUsername(storedUsername);
            setMyUserId(parseInt(localStorage.getItem('user_id')));
        }

    }, []);

    // hooks handle challenge/friend socket events
    
    return (
        <div>
            <h1>Welcome to the Home Page, {username}</h1>
            {!username && 
                <div>
                    <p>Please log in or sign up to continue.</p>
                    <Link to="/login">Log In</Link> | <Link to="/signup">Sign Up</Link>
                </div>
            }
            <div>
                <StatusMessage message={message || frMessage} />
                {username && <Button onClick={handleLogout} style={{ marginLeft: '10px' }}>Logout</Button>}
            </div>
            <div>
                {username && <Button onClick={()=>navigate(`/profile/${myUserId}`)}>My profile</Button>}
            </div>
            <div>
                {username && <Button onClick={handleJoinQueue}>Join a match</Button>}
            </div>
            <div>
                {username && <Button onClick={seeFriends}>See friends list</Button>}
                {username && <Button onClick={()=>navigate('/user-search')} style={{ marginLeft: 8 }}>Search Users</Button>}
            </div>


            {/* --- CHALLENGES UI --- */}
            {username && (
                <ListShell title="⚔️ Game Invites" emptyMessage="No game invites." loading={false}>
                    {challenges.length > 0 && (
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                            {challenges.map((c) => (
                                <ChallengeItem key={c.challenge_id} challenge={c} onAccept={async (id) => { try { const res = await acceptChallenge(id); if (res?.data?.game_id) navigate(`/game/${res.data.game_id}`); } catch (err) { setMessage(err.response?.data?.message || 'Failed to accept challenge'); } }} onDecline={async (id) => { try { await declineChallenge(id); } catch (err) { setMessage('Failed to decline challenge'); } }} />
                            ))}
                        </ul>
                    )}
                </ListShell>
            )}


            {/* 4. PENDING REQUESTS UI */}
            {username && (
                <div style={{ marginTop: '30px', borderTop: '1px solid #ccc', paddingTop: '10px' }}>
                    <h3>Pending Friend Requests</h3>
                    <ListShell loading={false} emptyMessage="No pending requests.">
                        {friendRequests.length === 0 ? (
                            null
                        ) : (
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                {friendRequests.map((req) => (
                                    <UserListItem key={req.id} user={req} actions={[{ label: 'Accept', variant: 'primary', onClick: () => acceptRequest(req.id) }, { label: 'Decline', variant: 'danger', onClick: () => declineRequest(req.id) }]} />
                                ))}
                            </ul>
                        )}
                    </ListShell>
                </div>
            )}

        </div>
    );
}