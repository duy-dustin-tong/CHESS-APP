// frontend/src/pages/friends-list.jsx

import { useState, useEffect } from 'react';
import api from '../api/api';
import { useNavigate } from 'react-router-dom';

export default function FriendsList() {
    const [friends, setFriends] = useState([]);
    const [loading, setLoading] = useState(true);
    const myUserId = localStorage.getItem('user_id');
    const navigate = useNavigate();

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
            fetchFriends();
        }
    }, [myUserId]);

    return (
        <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1>My Friends</h1>
                <button 
                    onClick={() => navigate('/')}
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
                        <li 
                            key={friend.id} 
                            style={{ 
                                padding: '15px', 
                                borderBottom: '1px solid #ddd',
                                display: 'flex',
                                justifyContent: 'space-between'
                            }}
                        >
                            <strong>{friend.username}</strong>
                            <span>Elo: {friend.elo || 'N/A'}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}