import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import api from "../api/api";

export default function Game() {
  const { gameId } = useParams();
  const [whiteId, setWhiteId] = useState("");
  const [blackId, setBlackId] = useState("");

  useEffect(() => { 
    const fetchGameData = async () => {
      try {
        const response = await api.get(`/games/games/${gameId}`);     
        setWhiteId(response.data.white_user_id);
        setBlackId(response.data.black_user_id);
      } 
      catch (error) {
        console.error("Error fetching game data:", error);
      }
    };

    fetchGameData();
  }, [gameId]);



  return (
    <div>
      <h1>Game ID: {gameId}</h1>
        <p>White Player ID: {whiteId}</p>
        <p>Black Player ID: {blackId}</p>

    </div>
  )


}