// frontend/src/pages/home.jsx
import { useState, useEffect, } from 'react';
import api from '../api/api';
import { Link, useNavigate } from 'react-router-dom';
import socket from '../api/sockets';



export default function Home() {
    
    const [username, setUsername] = useState(null);
    const [message, setMessage] = useState('');
    const [myUserId, setMyUserId] = useState(parseInt(localStorage.getItem('user_id')));
    const [friendRequests, setFriendRequests] = useState([]);
    const [challenges, setChallenges] = useState([]);



    const navigate = useNavigate();


    const fetchPendingChallenges = async () => {
        try {
            const response = await api.get('/challenges/challenges/pending');
            setChallenges(response.data);
        } catch (error) {
            console.error("Error fetching challenges:", error);
        }
    };

    // 1. FETCH PENDING REQUESTS
    const fetchFriendRequests = async () => {
        try {
            // Adjust this URL if your namespace/route differs
            // Assuming you have an endpoint that returns pending requests for the current user
            const response = await api.get(`/users/users/${myUserId}/friends/pending`); 
            setFriendRequests(response.data);
            console.log("Fetched friend requests:", response.data);   
        } catch (error) {
            console.error("Error fetching friend requests:", error);
        }

         
    };

    const respondChallenge = async (challengeId, responseType) => {
        try {
            const res = await api.post(`/challenges/respond_challenge/${challengeId}/${responseType}`);
            
            // Remove from state immediately
            setChallenges(prev => prev.filter(c => c.challenge_id !== challengeId));

            if (responseType === 'accept' && res.data.game_id) {
                navigate(`/game/${res.data.game_id}`);
            }
        } catch (error) {
            setMessage(error.response?.data?.message || "Action failed");
            // If 404 (expired/deleted), remove it from list
            if (error.response?.status === 404) {
                 setChallenges(prev => prev.filter(c => c.challenge_id !== challengeId));
            }
        }
    };


    // 2. ACCEPT REQUEST (PUT)
    const acceptRequest = async (requestId) => {
        try {
            await api.put(`/friendships/friendships/${requestId}`);
            setMessage("Friend request accepted!");
            // Remove from local list so UI updates immediately
            setFriendRequests(prev => prev.filter(req => req.id !== requestId));
        } catch (error) {
            setMessage("Failed to accept request.");
        }
    };

    // 3. DECLINE/REJECT REQUEST (DELETE)
    const declineRequest = async (requestId) => {
        try {
            await api.delete(`/friendships/friendships/${requestId}`);
            setMessage("Friend request declined.");
            setFriendRequests(prev => prev.filter(req => req.id !== requestId));
        } catch (error) {
            setMessage("Failed to decline request.");
        }
    };

    const handleLogout = () => {


        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('username');
        localStorage.removeItem('user_id');
        
        setMessage("Logged out successfully.");
        setUsername(null);

        socket.emit("deregister_user", { userId: myUserId });
    };

    const seeFriends = () => {
        navigate('/friends-list');
    }

    const joinQueue = async () => {
        try{
            setMessage("Joining matchmaking queue...");
            const response = await api.post('/matchmaking/matchmaking');
            if (response.data.message == "Paired") {

                navigate(`/game/${response.data.game_id}`);
                return;
            }
            setMessage(response.data.message);
            navigate('/waiting-room');
        }
        catch (error) {
            setMessage(error.response?.data?.message || "Failed to join matchmaking queue.");
        }
    } 
    


    useEffect(() => {
        const storedUsername = localStorage.getItem('username');
        if (storedUsername) {
            setUsername(storedUsername);
            setMyUserId(parseInt(localStorage.getItem('user_id')));
            socket.emit("register_user", { userId: myUserId});
            fetchFriendRequests();
            fetchPendingChallenges();
        }

    }, []);

    useEffect(() => {
        socket.on('friend_challenge_invite', (data) => {
            console.log("New Challenge received:", data);
            
            // Add new challenge to list (prevent duplicates just in case)
            setChallenges(prev => {
                if (prev.some(c => c.challenge_id === data.challenge_id)) return prev;
                return [...prev, data];
            });
        });

        socket.on('start_challenge', (data) => {
            navigate(`/game/${data.game_id}`);
        });

        return () => {
            socket.off('friend_challenge_invite');
            socket.off('start_challenge');
        };
    },[]);
    
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
                {message && <p>{message}</p>}
            
                {username && <button onClick={handleLogout} style={{ marginLeft: '10px' }}>Logout</button>}
            </div>
            <div>
                {username && <button onClick={joinQueue}> join a match</button>}
            </div>
            <div>
                {username && <button onClick={seeFriends}> see friends list</button>}
            </div>


            {/* --- CHALLENGES UI --- */}
            {username && challenges.length > 0 && (
                <div style={{ marginTop: '20px', border: '2px solid gold', padding: '15px', borderRadius: '8px', backgroundColor: '#fffbe6' }}>
                    <h3 style={{margin: '0 0 10px 0'}}>⚔️ Game Invites</h3>
                    
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        {challenges.map((c) => (
                            <li key={c.challenge_id} style={{ 
                                display: 'flex', 
                                justifyContent: 'space-between', 
                                alignItems: 'center', 
                                marginBottom: '10px', 
                                padding: '10px', 
                                background: 'white',
                                border: '1px solid #ddd' 
                            }}>
                                <span>
                                    <strong>{c.username}</strong> has challenged you to a game!
                                </span>
                                <div>
                                    <button 
                                        onClick={() => respondChallenge(c.challenge_id, 'accept')} 
                                        style={{ backgroundColor: '#4CAF50', color: 'white', border:'none', padding: '8px 12px', marginRight: '5px', cursor: 'pointer' }}
                                    >
                                        Accept
                                    </button>
                                    <button 
                                        onClick={() => respondChallenge(c.challenge_id, 'decline')} 
                                        style={{ backgroundColor: '#f44336', color: 'white', border:'none', padding: '8px 12px', cursor: 'pointer' }}
                                    >
                                        Decline
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}


            {/* 4. PENDING REQUESTS UI */}
            {username && (
                <div style={{ marginTop: '30px', borderTop: '1px solid #ccc', paddingTop: '10px' }}>
                    <h3>Pending Friend Requests</h3>
                    {friendRequests.length === 0 ? (
                        <p>No pending requests.</p>
                    ) : (
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                            {friendRequests.map((req) => (
                                <li key={req.id} style={{ marginBottom: '10px', padding: '10px', border: '1px solid #eee', borderRadius: '5px' }}>
                                    <span>User {req.username} wants to be friends!</span>
                                    <div style={{ marginTop: '5px' }}>
                                        <button 
                                            onClick={() => acceptRequest(req.id)}
                                            style={{ backgroundColor: '#28a745', color: 'white', border: 'none', marginRight: '5px', padding: '5px 10px', cursor: 'pointer' }}
                                        >
                                            Accept
                                        </button>
                                        <button 
                                            onClick={() => declineRequest(req.id)}
                                            style={{ backgroundColor: '#dc3545', color: 'white', border: 'none', padding: '5px 10px', cursor: 'pointer' }}
                                        >
                                            Decline
                                        </button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}

        </div>
    );
}