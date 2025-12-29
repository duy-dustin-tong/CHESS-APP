// frontend/src/pages/friends-list.jsx

import { useState, useEffect } from 'react';
import api from '../api/api';
import socket from '../api/sockets';
import { useNavigate } from 'react-router-dom';

export default function FriendsList() {
    const [friends, setFriends] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusMessage, setStatusMessage] = useState('');
    const [waitingChallenge, setWaitingChallenge] = useState(false);
    const myUserId = parseInt(localStorage.getItem('user_id'));
    const navigate = useNavigate();


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
            setFriends(prev => prev.filter(f => f.id !== friendId));
        } catch (error) {
            alert("Failed to remove friend");
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



    useEffect(() => {
        const fetchFriends = async () => {
            try {
                // Calling your existing GET /users/<id>/friends endpoint
                const response = await api.get(`/users/users/${myUserId}/friends`);
                setFriends(response.data);
            } catch (error) {
                console.error("Error fetching friends:", error);
            } finally {
                setLoading(false);
            }
        };

        if (myUserId) {
            socket.emit("register_user", { userId: myUserId});
            fetchFriends();
        }
    }, [myUserId]);

    useEffect(() => {


        socket.on('start_challenge', (data) => {
            navigate(`/game/${data.game_id}`);
        });

        return () => {
            socket.off('start_challenge');
        };
    },[]);

    return (
        <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                
                <h1>My Friends</h1>
                <button 
                    onClick={backToHome}
                    style={{ padding: '8px 16px', cursor: 'pointer' }}
                >
                    Back to Home
                </button>
            </div>

            <hr />

            {loading ? (
                <p>Loading friends...</p>
            ) : friends.length === 0 ? (
                <p>You haven't added any friends yet.</p>
            ) : (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {friends.map((friend) => (
                        <li key={friend.id} style={{ 
                            padding: '15px', borderBottom: '1px solid #ddd',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                        }}>
                            <div>
                                <strong style={{ fontSize: '1.1em' }}>{friend.username}</strong>
                                <div style={{ color: '#666' }}>Elo: {friend.elo}</div>
                            </div>

                            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                {/* Challenge Buttons */}
                                <div style={{ display: 'flex', border: '1px solid #ccc', borderRadius: '4px', overflow: 'hidden' }}>
                                    <button 
                                        onClick={() => sendChallenge(friend.id)}
                                        style={{ padding: '8px 12px', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                                        title="Challenge"
                                    >
                                        Challenge
                                    </button>
                                    
                                </div>

                                {/* Remove Button */}
                                <button 
                                    onClick={() => removeFriend(friend.id)}
                                    style={{ padding: '8px', color: '#dc3545', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2em' }}
                                    title="Remove Friend"
                                >
                                    🗑️
                                </button>
                            </div>
                        </li>
                    ))}
                </ul>
            )}
            {waitingChallenge && 
                <button 
                    onClick={cancelChallenge}
                    style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px' }}
                >
                    Cancel Challenge
                </button>
            }
            {statusMessage && <p style={{ marginTop: '20px', color: '#007bff' }}>{statusMessage}</p>}
        </div>
    );
}