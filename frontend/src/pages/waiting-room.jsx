// frontend/src/pages/waiting-room.jsx
import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom"; 
import socket from "../api/sockets";
import api from "../api/api";
import StatusMessage from '../components/StatusMessage';
import Button from '../components/Button';
import useMatchmaking from '../hooks/useMatchmaking';
import useChallengeActions from '../hooks/useChallengeActions';
import ChallengeItem from '../components/ChallengeItem';
import ListShell from '../components/ListShell';

export default function WaitingRoom() {
  const [message, setMessage] = useState("Waiting for an opponent to join...");
  const [myUserId, setMyUserId] = useState(parseInt(localStorage.getItem('user_id')));
  const navigate = useNavigate();  
  const { leaveQueue, status } = useMatchmaking();
  const handleStart = useCallback((data) => {
    setMessage('Match found! Redirecting to game...');
    setTimeout(() => navigate(`/game/${data.game_id}`), 500);
  }, [navigate]);

  const { challenges, acceptChallenge, declineChallenge } = useChallengeActions(myUserId, handleStart);
  


  useEffect(() => {
    socket.on("start_game", (data) => {
      setMessage("Match found! Redirecting to game...");
      // Small delay or check to prevent double navigation 
      // if the HTTP response also tries to redirect
      setTimeout(() => {
        navigate(`/game/${data.game_id}`);
      }, 500);
    });

    return () => {
      socket.off("start_game");
    };
  },[navigate]);

  useEffect(() => {
    if(myUserId){
      socket.emit("register_user", { userId: myUserId});
    } 

  }, []);

  


  return(
    <div>
      <h1>Waiting Room</h1>
        <StatusMessage message={message} />

      <ListShell title="Pending Challenges" emptyMessage="No pending challenges." loading={false}>
        {challenges && challenges.length > 0 && (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {challenges.map((c) => (
              <ChallengeItem key={c.challenge_id} challenge={c} onAccept={async (id) => {
                try {
                  const res = await acceptChallenge(id);
                  if (res?.data?.game_id) navigate(`/game/${res.data.game_id}`);
                } catch (err) {
                  setMessage(err.response?.data?.message || 'Failed to accept challenge');
                }
              }} onDecline={async (id) => {
                try { await declineChallenge(id); } catch (err) { setMessage('Failed to decline challenge'); }
              }} />
            ))}
          </ul>
        )}
      </ListShell>

      <div style={{ marginTop: 12 }}>
        <Button onClick={async () => { try { await leaveQueue(); navigate('/'); } catch { navigate('/'); } }}>Cancel and Return Home</Button>
      </div>
    </div>
  )
};