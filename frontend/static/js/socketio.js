export function connectSocket(callbacks) {
    const socket = io();

    callbacks.forEach(([eventName, callback]) => {
        console.log(`Listening for event: ${eventName}`);
        socket.on(eventName, callback);
    });

    socket.on('error', e => console.error(e.msg));
    return socket;
}
