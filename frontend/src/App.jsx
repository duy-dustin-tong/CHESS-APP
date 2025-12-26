// frontend/src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SignUp from './pages/signup.jsx';
import LogIn from './pages/login.jsx';
import Home from './pages/home.jsx';
import Game from './pages/game.jsx';
import WaitingRoom from './pages/waiting-room.jsx';
import FriendsList from './pages/friends-list.jsx';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/signup" element={<SignUp />} />
        <Route path="/login" element={<LogIn />} />
        <Route path="/" element={<Home />} />
        <Route path="/game/:gameId" element={<Game />} />
        <Route path="/waiting-room" element={<WaitingRoom />} />
        <Route path="/friends-list" element={<FriendsList />} />
      </Routes>
    </Router>
  );
}