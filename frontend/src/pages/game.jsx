// frontend/src/pages/game.jsx
import { useParams } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import api from "../api/api";
import socket from "../api/sockets";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";

export default function Game() {
  const { gameId } = useParams();
  const [whiteId, setWhiteId] = useState("");
  const [blackId, setBlackId] = useState("");
  const [myUserId, setMyUserId] = useState(localStorage.getItem("user_id"));

  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;

  // track the current position of the chess game in state to trigger a re-render of the chessboard
  const [chessPosition, setChessPosition] = useState(chessGame.fen());
  const [moveFrom, setMoveFrom] = useState('');
  const [optionSquares, setOptionSquares] = useState({});

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
      alert(`Game Over! Winner: ${data.winner_id || "Draw"}`);
    });

    return () => {
      socket.off("move_made");
      socket.off("game_over");
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

  // handle piece drop
  function onPieceDrop({
    sourceSquare,
    targetSquare
  }) {


    // Basic turn check: Don't allow moving if it's not your turn
    const turn = chessGame.turn(); // 'w' or 'b'
    if ((turn === 'w' && myUserId !== whiteId) || (turn === 'b' && myUserId !== blackId)) {
      return false;
    }


    // type narrow targetSquare potentially being null (e.g. if dropped off board)
    if (!targetSquare) {
      return false;
    }

    // try to make the move according to chess.js logic
    try {
      chessGame.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q' // always promote to a queen for example simplicity
      });

      // update the position state upon successful move to trigger a re-render of the chessboard
      setChessPosition(chessGame.fen());

      // send the move to the backend in UCI format
      const moveUCI = sourceSquare + targetSquare + (chessGame.get(targetSquare)?.type === 'p' && (targetSquare[1] === '8' || targetSquare[1] === '1') ? 'q' : '');
      submitMove(moveUCI);  

      // clear moveFrom and optionSquares
      setMoveFrom('');
      setOptionSquares({});



      // return true as the move was successful
      return true;
    } catch {
      // return false as the move was not successful
      return false;
    }
  }

  // set the chessboard options
  const chessboardOptions = {
    onPieceDrop,
    onSquareClick,
    position: chessPosition,
    squareStyles: optionSquares,
    id: 'click-or-drag-to-move'
  };


  return (
    <div>
      <h1>Game ID: {gameId}</h1>
        <p>White Player ID: {whiteId}</p>
        <p>Black Player ID: {blackId}</p>

        <Chessboard options={chessboardOptions} />

    </div>
  )


}