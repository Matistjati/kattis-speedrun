export function connectSocket(callbacks) {
    const socket = io();

    callbacks.forEach(([eventName, callback]) => {
        socket.on(eventName, callback);
    });

    socket.on('error', e => console.error(e.msg));
    return socket;
}
