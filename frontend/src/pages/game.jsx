// frontend/src/pages/game.jsx
import { useParams } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import api from "../api/api";
import socket from "../api/sockets";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import { useNavigate } from "react-router-dom";
import GameControls from '../components/GameControls';

export default function Game() {
  const { gameId } = useParams();
  const [whiteId, setWhiteId] = useState("");
  const [blackId, setBlackId] = useState("");
  const [myUserId, setMyUserId] = useState(localStorage.getItem("user_id"));
  const [friendRequestSent, setFriendRequestSent] = useState(false);
  const [pendingPromotion, setPendingPromotion] = useState(null);
  // Will store: { from: 'a7', to: 'a8', color: 'w' }

  const [drawOfferedBy, setDrawOfferedBy] = useState(null); 

  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;
  const boardOrientation = myUserId === blackId ? "black" : "white";

  // track the current position of the chess game in state to trigger a re-render of the chessboard
  const [chessPosition, setChessPosition] = useState(chessGame.fen());
  const [moveFrom, setMoveFrom] = useState('');
  const [optionSquares, setOptionSquares] = useState({});

  const navigate = useNavigate();

  useEffect(() => {
    // Join the game room
    socket.emit("join_game", { gameId });

    // Listen for moves from the server
    socket.on("move_made", (data) => {
      // Logic: Only apply if the move isn't already reflected (prevents double moves)
      if (chessGame.fen() !== data.current_fen) {
        chessGame.move(data.move);
        setChessPosition(chessGame.fen());
      }
    });

    socket.on("game_over", (data) => {

      if(data.reason === "resignation") {
        alert(`Game Over! Player ${data.winner_id} wins by resignation.`);
      } else
      alert(`Game Over! Winner: ${data.winner_id || "Draw"}`);

      socket.emit("leave_game", { gameId });
      navigate("/")
    });

    socket.on("draw_offered", (data) => {
      console.log("Draw offered by:", typeof data.offerer_id);
      console.log("My user ID:", typeof myUserId);

      if (data.offerer_id !== parseInt(myUserId)) {
        setDrawOfferedBy(data.offerer_id);
      }
    });

    socket.on("draw_declined", () => {
      alert("Draw offer declined.");
      setDrawOfferedBy(null);
    });

    return () => {
      socket.emit("leave_game", { gameId });
      socket.off("move_made");
      socket.off("game_over");
      socket.off("draw_offered");
      socket.off("draw_declined");
    };
  }, [gameId]);


  // 2. FETCH INITIAL GAME STATE
  useEffect(() => { 
    const fetchGameData = async () => {
      try {
        const response = await api.get(`/games/games/${gameId}`);     
        setWhiteId(response.data.white_user_id);
        setBlackId(response.data.black_user_id);
        
        // If game is already in progress, sync board with FEN from DB
        if (response.data.current_fen) {
          chessGame.load(response.data.current_fen);
          setChessPosition(chessGame.fen());
        }
      } catch (error) {
        console.error("Error fetching game data:", error);
      }
    };
    fetchGameData();
    const storedId = localStorage.getItem("user_id");
    setMyUserId(parseInt(storedId, 10));
  }, [gameId]);

  // 3. SEND MOVE TO BACKEND
  const submitMove = async (moveUCI) => {
    try {
      // We use the 'put' route you created: /games/<game_id>/<move>
      await api.put(`/games/games/${gameId}/${moveUCI}`);
    } catch (error) {
      console.error("Move rejected by server:", error);
      // Revert board if server rejects it
      const response = await api.get(`/games/games/${gameId}`);
      chessGame.load(response.data.current_fen);
      setChessPosition(chessGame.fen());
    }
  };

  const handleAddFriend = async () => {
    const opponentId = myUserId === whiteId ? blackId : whiteId;
    
    try {
        await api.post('/friendships/friendships', {
            user1_id: myUserId,
            user2_id: opponentId
        });
        setFriendRequestSent(true);
      return { ok: true };
    } catch (error) {
        console.error("Error sending friend request:", error);
      return { ok: false, message: error.response?.data?.message || "Failed to send request." };
    }
  };

  const handleResign = async () => {
    if (window.confirm("Are you sure you want to resign?")) {
      try {
        await api.post(`/games/games/${gameId}/resign`);
        // Note: We don't need to manually update state here because 
        // the backend will emit a 'game_over' socket event.
      } catch (error) {
        console.error("Error resigning:", error);
        alert("Could not process resignation.");
      }
    }
  };

  const offerDraw = async () => {
    try {
      await api.post(`/games/games/${gameId}/offer-draw`);
      alert("Draw offer sent.");
    } catch (err) {
      console.error(err);
    }
  };

  const respondToDraw = async (accepted) => {
    try {
      await api.post(`/games/games/${gameId}/respond-draw`, { accepted });
      setDrawOfferedBy(null);
    } catch (err) {
      console.error(err);
    }
  };

  function getMoveOptions(square) {
    // get the moves for the square
    const moves = chessGame.moves({
      square,
      verbose: true
    });

    // if no moves, clear the option squares
    if (moves.length === 0) {
      setOptionSquares({});
      return false;
    }

    // create a new object to store the option squares
    const newSquares = {};

    // loop through the moves and set the option squares
    for (const move of moves) {
      newSquares[move.to] = {
        background: chessGame.get(move.to) && chessGame.get(move.to)?.color !== chessGame.get(square)?.color ? 'radial-gradient(circle, rgba(0,0,0,.1) 85%, transparent 85%)' // larger circle for capturing
        : 'radial-gradient(circle, rgba(0,0,0,.1) 25%, transparent 25%)',
        // smaller circle for moving
        borderRadius: '50%'
      };
    }

    // set the square clicked to move from to yellow
    newSquares[square] = {
      background: 'rgba(255, 255, 0, 0.4)'
    };

    // set the option squares
    setOptionSquares(newSquares);

    // return true to indicate that there are move options
    return true;
  }

  function onSquareClick({
    square,
    piece
  }) {

    const turn = chessGame.turn();
    const isMyTurn = (turn === 'w' && myUserId === whiteId) || (turn === 'b' && myUserId === blackId);
    if (!isMyTurn) return;



    // piece clicked to move
    if (!moveFrom && piece) {
      // get the move options for the square
      const hasMoveOptions = getMoveOptions(square);

      // if move options, set the moveFrom to the square
      if (hasMoveOptions) {
        setMoveFrom(square);
      }

      // return early
      return;
    }

    // square clicked to move to, check if valid move
    const moves = chessGame.moves({
      square: moveFrom,
      verbose: true
    });
    const foundMove = moves.find(m => m.from === moveFrom && m.to === square);

    // not a valid move
    if (!foundMove) {
      // check if clicked on new piece
      const hasMoveOptions = getMoveOptions(square);

      // if new piece, setMoveFrom, otherwise clear moveFrom
      setMoveFrom(hasMoveOptions ? square : '');

      // return early
      return;
    }

    // Detect if this move is a promotion (chess.js flags it)
    if (foundMove.promotion) {
      setPendingPromotion({
        from: moveFrom,
        to: square,
        color: turn, // 'w' or 'b'
      });
      return; // STOP here. Wait for user to select piece in the UI.
    }

    // is normal move
    try {
      chessGame.move({
        from: moveFrom,
        to: square,
        promotion: 'q'
      });
      submitMove(foundMove.from + foundMove.to + (foundMove.promotion ? foundMove.promotion : ''));
    } catch {
      // if invalid, setMoveFrom and getMoveOptions
      const hasMoveOptions = getMoveOptions(square);

      // if new piece, setMoveFrom, otherwise clear moveFrom
      if (hasMoveOptions) {
        setMoveFrom(square);
      }

      // return early
      return;
    }

    // update the position state
    setChessPosition(chessGame.fen());


    // clear moveFrom and optionSquares
    setMoveFrom('');
    setOptionSquares({});
  }


  const finalizePromotion = (promotionPiece) => {
    if (!pendingPromotion) return;

    try {
      chessGame.move({
        from: pendingPromotion.from,
        to: pendingPromotion.to,
        promotion: promotionPiece, // 'q', 'r', 'b', or 'n'
      });

      // Update board
      setChessPosition(chessGame.fen());

      // Send to backend (e.g., "a7a8q")
      submitMove(pendingPromotion.from + pendingPromotion.to + promotionPiece);
      
      // Cleanup
      setPendingPromotion(null);
      setMoveFrom('');
      setOptionSquares({});
    } catch (error) {
      console.error("Promotion failed:", error);
      setPendingPromotion(null); // Cancel move on error
    }
  };

  // set the chessboard options
  const chessboardOptions = {

    onSquareClick,
    position: chessPosition,
    squareStyles: optionSquares,
    boardOrientation: boardOrientation,
    id: 'click-to-move',
  };

  const opponentId = myUserId === whiteId ? blackId : whiteId;
  
  return (
    <div>
      <h1>Game ID: {gameId}</h1>
      <p>White Player ID: {whiteId}</p>
      <p>Black Player ID: {blackId}</p>


      <GameControls
        onResign={handleResign}
        onOfferDraw={offerDraw}
        onAddFriend={handleAddFriend}
        drawOfferedBy={drawOfferedBy}
        respondToDraw={respondToDraw}
        friendRequestSent={friendRequestSent}
        myUserId={myUserId}
        opponentId={opponentId}
        statusMessage={null}
      />

      <Chessboard options={chessboardOptions} />


      {/* CUSTOM PROMOTION MODAL */}
      {pendingPromotion && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'rgba(255,255,255,0.9)',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
          zIndex: 100,
          display: 'flex',
          gap: '10px'
        }}>
          <p style={{ width: '100%', textAlign: 'center', marginBottom: '10px' }}>Promote to:</p>
          {['q', 'r', 'b', 'n'].map((p) => (
            <button
              key={p}
              onClick={() => finalizePromotion(p)}
              style={{
                padding: '10px',
                cursor: 'pointer',
                fontSize: '24px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                background: 'white'
              }}
            >
              {/* Simple unicode pieces or text */}
              {pendingPromotion.color === 'w' 
                ? { q: '♕', r: '♖', b: '♗', n: '♘' }[p] 
                : { q: '♛', r: '♜', b: '♝', n: '♞' }[p]
              }
            </button>
          ))}
        </div>
      )}

    </div>
  )


}