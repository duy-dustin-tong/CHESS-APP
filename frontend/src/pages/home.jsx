import { useState, useEffect } from 'react';
import api from '../api/api';
import { Link, useNavigate } from 'react-router-dom';


export default function Home() {
    
    const [username, setUsername] = useState(null);
    const [message, setMessage] = useState('');

    const navigate = useNavigate();

    const handleLogout = () => {


        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('username');
        localStorage.removeItem('user_id');
        
        setMessage("Logged out successfully.");
        setUsername(null);
    };

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
        }   
    }, []);
    
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

        </div>
    );
}