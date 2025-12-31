// frontend/src/pages/profile.jsx

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/api';
import ListShell from '../components/ListShell';
import UserListItem from '../components/UserListItem';
import Button from '../components/Button';
import usePaginatedFetch from '../hooks/usePaginatedFetch';



    

export default function Profile() {
    const { userId } = useParams();
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [friends, setFriends] = useState([]);
    const [myFriends, setMyFriends] = useState([]);
    const [commonFriends, setCommonFriends] = useState([]);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [friendRequestSent, setFriendRequestSent] = useState(false);
    const [friendRequestLoading, setFriendRequestLoading] = useState(false);

    const viewerId = localStorage.getItem('user_id') ? parseInt(localStorage.getItem('user_id')) : null;

    useEffect(() => {
        let cancelled = false;
        const fetchAll = async () => {
            setLoading(true);
            setError(null);
            try {
            const endpoints = [
                api.get(`/users/users/${userId}`),
                api.get(`/users/users/${userId}/friends`),
                api.get(`/users/users/${userId}/history`),
            ];

            if (viewerId) endpoints.push(api.get(`/users/users/${viewerId}/friends`));
            const results = await Promise.all(endpoints);

            const userRes = results[0].data;
            const friendsRes = results[1].data || [];
            const historyRes = results[2].data || [];
            const myFriendsRes = viewerId ? results[3].data || [] : [];

            if (cancelled) return;

            setUser(userRes);
            setFriends(friendsRes);
            setHistory(historyRes);
            setMyFriends(myFriendsRes);

            // compute common friends by id
            if (viewerId) {
                const myIds = new Set(myFriendsRes.map((f) => f.id));
                const common = friendsRes.filter((f) => myIds.has(f.id));
                setCommonFriends(common);
            } else {
                setCommonFriends([]);
            }
            } catch (err) {
                setError(err.response?.data?.message || 'Failed to load profile');
            } finally {
                setLoading(false);
            }
        };

        fetchAll();
        return () => { cancelled = true; };
    }, [userId, viewerId]);

    const displayElo = (val) => {
        if (val == null) return 'N/A';
        if (typeof val === 'object') return val.elo ?? 'N/A';
        return val;
    };

    return (
    <div>
        <h1>Profile</h1>

        <div style={{ marginBottom: 12 }}>
        <Button onClick={() => navigate(-1)}>Back</Button>
        {viewerId === parseInt(userId) && (
            <Button onClick={() => navigate('/edit-account')} style={{ marginLeft: 8 }}>Edit Account</Button>
        )}
        {/* Show Add Friend when viewer is logged in, not viewing own profile, and not already friends */}
        {viewerId && viewerId !== parseInt(userId) && !friends.some((f) => f.id === viewerId) && !friendRequestSent && (
            <Button
            onClick={async () => {
                setFriendRequestLoading(true);
                try {
                await api.post('/friendships/friendships', { user1_id: viewerId, user2_id: parseInt(userId) });
                setFriendRequestSent(true);
                } catch (err) {
                setError(err.response?.data?.message || 'Failed to send friend request');
                } finally {
                setFriendRequestLoading(false);
                }
            }}
            style={{ marginLeft: 8 }}
            disabled={friendRequestLoading}
            >
            {friendRequestLoading ? 'Sending...' : 'Add Friend'}
            </Button>
        )}
        {friendRequestSent && <span style={{ marginLeft: 12, color: 'green' }}>Friend request sent</span>}
        </div>

        <ListShell loading={loading} emptyMessage="No profile found">
        {error && <div style={{ color: 'red' }}>{error}</div>}

        {user && (
            <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 6 }}>
            <div><strong>User ID:</strong> {userId}</div>
            <div><strong>Username:</strong> {user.username}</div>
            <div><strong>Elo:</strong> {displayElo(user.elo)}</div>
            </div>
        )}

        <div style={{ display: 'flex', gap: 20, marginTop: 16 }}>
            <div style={{ flex: 1 }}>
            <h3>Game History</h3>
            <ListShell emptyMessage="No games.">
                <ul style={{ listStyle: 'none', padding: 0 }}>
                {history.map((g) => (
                    <li key={g.id} style={{ marginBottom: 10, border: '1px solid #eee', padding: 8, borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div><strong>{new Date(g.created_at).toLocaleString()}</strong></div>
                        <div>Opponent: <Link to={`/profile/${g.white_user_id === parseInt(userId) ? g.black_user_id : g.white_user_id}`}>{g.white_user_id === parseInt(userId) ? g.black_username : g.white_username}</Link></div>
                        <div>Elo: {g.white_user_id === parseInt(userId) ? g.white_elo : g.black_elo}</div>
                        <div>Opponent elo: {g.white_user_id === parseInt(userId) ? g.black_elo : g.white_elo}</div>
                        <div>Moves: {g.moves.join(' ')}</div>
                        <div>{g.winner_id == userId ? 'Won' : (g.winner_id == null ? 'Draw' : 'Lost')}</div>
                    </div>
                    </li>
                ))}
                </ul>
            </ListShell>
            </div>

            <div style={{ width: 320 }}>
            <h3>Friends</h3>
            <ListShell emptyMessage="No friends.">
                <ul style={{ listStyle: 'none', padding: 0 }}>
                {friends.map((f) => (
                    <UserListItem key={f.id} user={f} showElo />
                ))}
                </ul>
            </ListShell>

            {userId != viewerId && <>
                <h4 style={{ marginTop: 16 }}>Common Friends</h4>
                <ListShell emptyMessage="No common friends.">
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {commonFriends.map((f) => (
                    <UserListItem key={f.id} user={f} showElo />
                    ))}
                </ul>
                </ListShell>
            </>}
            </div>
        </div>
        </ListShell>
    </div>
    );
}
