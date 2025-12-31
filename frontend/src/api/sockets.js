// frontend/src/api/sockets.js
import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';

function createRawSocket() {
	const token = localStorage.getItem('access_token');
	return io(SOCKET_URL, { auth: { token }, autoConnect: true });
}

let raw = createRawSocket();

// forwarding proxy so existing imports keep working even after we recreate
const socket = {
	on: (...args) => raw.on(...args),
	off: (...args) => raw.off(...args),
	emit: (...args) => raw.emit(...args),
	disconnect: (...args) => raw.disconnect(...args),
	connect: (...args) => raw.connect(...args),
	io: () => raw,
	replaceRaw: (newRaw) => { raw = newRaw; },
};

export function recreateSocket() {
	try { raw.disconnect(); } catch (e) { /* ignore */ }
	const newRaw = createRawSocket();
	socket.replaceRaw(newRaw);
	return newRaw;
}

// When access_token changes in other tabs/windows, recreate socket to use new token
if (typeof window !== 'undefined') {
	window.addEventListener('storage', (e) => {
		if (e.key === 'access_token') {
			recreateSocket();
		}
	});
}

export default socket;