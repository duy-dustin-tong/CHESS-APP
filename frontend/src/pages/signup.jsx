// frontend/src/pages/signup.jsx
import { useState } from 'react';
import api from '../api/api';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../components/Button';

export default function SignUp() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');

    const navigate = useNavigate();

    const handleSignUp = async (e) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            setMessage("Passwords do not match");
            return;
        }   
        try {
            const response = await api.post(`/auth/signup`, { email, username, password });
            if (response.status === 201) {
                setMessage("Sign up successful! You can now log in.");
            }
            navigate('/login');
        } catch (error) {
            console.error('Signup error', error);
            setMessage(error.response?.data?.message || "Sign up failed");
        }
    };

    return (
        <div style={{ padding: '40px', fontFamily: 'Arial' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1>Sign Up</h1>
                <Button onClick={() => navigate('/')}>Home</Button>
            </div>
            <p>Status: {message}</p>
            <form onSubmit={handleSignUp}>
                <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
                <br /><br />
                <input type="username" placeholder="Username" onChange={(e) => setUsername(e.target.value)} />
                <br /><br />
                <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
                <br /><br />
                <input type="password" placeholder="Confirm Password" onChange={(e) => setConfirmPassword(e.target.value)} />
                <br /><br />
                <button type="submit">Sign Up</button>
            </form>
            <br />
            <Link to="/login">Already have an account? Log in here.</Link>
        </div>
    );
}