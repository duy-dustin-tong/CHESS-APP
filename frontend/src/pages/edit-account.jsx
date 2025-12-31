import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import api from '../api/api';

export default function EditAccount() {
  const navigate = useNavigate();
  const viewerId = localStorage.getItem('user_id') ? parseInt(localStorage.getItem('user_id')) : null;

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!viewerId) return;
    let cancelled = false;
    const fetchUser = async () => {
      try {
        const res = await api.get(`/users/users/${viewerId}`);
        if (cancelled) return;
        setUsername(res.data.username || '');
        setEmail(res.data.email || '');
      } catch (err) {
        setMessage(err.response?.data?.message || 'Failed to load account');
      }
    };
    fetchUser();
    return () => { cancelled = true; };
  }, [viewerId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!viewerId) {
      setMessage('Not logged in');
      return;
    }
    if (password && password !== confirmPassword) {
      setMessage('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const payload = { };
      if (username) payload.username = username;
      if (email) payload.email = email;
      if (password) payload.password = password;

      await api.put(`/users/users/${viewerId}`, payload);
      setMessage('Account updated successfully');
      setTimeout(() => navigate(`/profile/${viewerId}`), 800);
    } catch (err) {
      setMessage(err.response?.data?.message || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, fontFamily: 'Arial' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Edit Account</h1>
        <Button onClick={() => navigate('/')}>Home</Button>
      </div>
      <p>{message}</p>
      {!viewerId ? (
        <div>Please log in to edit your account.</div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div>
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <br />
          <div>
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <br />
          <div>
            <input type="password" placeholder="New Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <br />
          <div>
            <input type="password" placeholder="Confirm Password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          <br />
          <button type="submit" disabled={loading}>{loading ? 'Saving...' : 'Save Changes'}</button>
        </form>
      )}
    </div>
  );
}
