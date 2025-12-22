import { useState } from 'react';
import api from '../api/api';
import { Link, useNavigate } from 'react-router-dom';


export default function LogIn() {

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');


  const navigate = useNavigate();
  


  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post(`/auth/login`, { email, password });

      const { access_token, refresh_token, username } = response.data;


      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('username', username);


      setMessage("Logged in!");
      navigate('/');
    } 
    catch {
      setMessage("Login failed or incorrect credentials.");
    }
  };

  


  return (
    <div style={{ padding: '40px', fontFamily: 'Arial' }}>
      <h1>Log in</h1>
      <p>Status: {message}</p>

      
        <form onSubmit={handleLogin}>
          <input type="username" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
          <br /><br />
          <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
          <br /><br />
          <button type="submit">Login</button>
        </form>
      
        <Link to="/signup">Don't have an account? Sign up here.</Link>
      
    </div>
  );
}

