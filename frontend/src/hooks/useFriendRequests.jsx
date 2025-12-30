import { useState, useEffect } from 'react';
import api from '../api/api';
import socket from '../api/sockets';

export default function useFriendRequests(myUserId) {
  const [friendRequests, setFriendRequests] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!myUserId) return;

    const fetchRequests = async () => {
      try {
        const res = await api.get(`/users/users/${myUserId}/friends/pending`);
        setFriendRequests(res.data || []);
      } catch (err) {
        console.error('Failed to fetch friend requests', err);
      }
    };

    fetchRequests();

    const onIncoming = (data) => {
      setFriendRequests((prev) => (prev.some((r) => r.id === data.id) ? prev : [...prev, data]));
    };

    socket.on('friend_request', onIncoming);

    return () => {
      socket.off('friend_request', onIncoming);
    };
  }, [myUserId]);

  const acceptRequest = async (requestId) => {
    try {
      await api.put(`/friendships/friendships/${requestId}`);
      setMessage('Friend request accepted!');
      setFriendRequests((prev) => prev.filter((r) => r.id !== requestId));
    } catch (err) {
      setMessage('Failed to accept request.');
    }
  };

  const declineRequest = async (requestId) => {
    try {
      await api.delete(`/friendships/friendships/${requestId}`);
      setMessage('Friend request declined.');
      setFriendRequests((prev) => prev.filter((r) => r.id !== requestId));
    } catch (err) {
      setMessage('Failed to decline request.');
    }
  };

  return { friendRequests, acceptRequest, declineRequest, message, setMessage, setFriendRequests };
}
