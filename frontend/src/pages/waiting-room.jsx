import { useState, useEffect } from "react";
import api from "../api/api";
import { useNavigate } from "react-router-dom"; 

export default function WaitingRoom() {
  const [message, setMessage] = useState("Waiting for an opponent to join...");
  const navigate = useNavigate();   

  useEffect(() => {
    const checkGameStatus = async () => {
        try {
            const response = await api.get('/matchmaking/status');
            if (response.data.paired) {
                navigate(`/game/${response.data.game_id}`);
            }
        } 
        catch (error) {
            console.error("Error checking game status:", error);
            setMessage("Error checking matchmaking status.");
        }
    };
    checkGameStatus();
    const intervalId = setInterval(checkGameStatus, 3000);
    return () => clearInterval(intervalId);
  },[navigate]);


  return(
    <div>
      <h1>Waiting Room</h1>
        <p>{message}</p>
    </div>
  )
};