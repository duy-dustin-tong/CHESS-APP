import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom"; 
import socket from "../api/sockets";
import api from "../api/api";

export default function WaitingRoom() {
  const [message, setMessage] = useState("Waiting for an opponent to join...");
  const navigate = useNavigate();  
  
  

  const leaveQueue = async () => {
    try {
      setMessage("Leaving matchmaking queue...");
      const response = await api.delete('/matchmaking/matchmaking');

      setMessage(response.data.message);
      navigate('/');


    } catch (error) {
      setMessage("Failed to leave matchmaking queue.", error);
    }
  };

  useEffect(() => {

    const myUserId = localStorage.getItem("user_id");

    if (myUserId) {
      socket.emit("register_user", { userId: myUserId });
    }

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

  


  return(
    <div>
      <h1>Waiting Room</h1>
        <p>{message}</p>
      <button onClick={leaveQueue}>Cancel and Return Home</button>
    </div>
  )
};