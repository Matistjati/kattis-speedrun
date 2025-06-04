import { connectSocket } from './socketio.js';

const socket = connectSocket([
        ['queue_data', (data) => {
            let queue_element = document.getElementById('waiting-submissions');
            console.log(queue_element)
            queue_element.innerHTML = '';

            data["pending"].forEach(element => {
                const submission = document.createElement('tr');
                submission.innerHTML = `
                    <td>${element.problem_difficulty}</td>
                    <td>${element.problem_shortname}</td>
                    <td>${element.user_name}</td>
                    <td>${element.submitted_at}</td>
                    <td>${element.language}</td>
                `;
                queue_element.appendChild(submission);
            });

            data["judged"].forEach(element => {
                const submission = document.createElement('tr');
                submission.innerHTML = `
                    <td>${element.problem_difficulty}</td>
                    <td>${element.problem_shortname}</td>
                    <td>${element.user_name}</td>
                    <td>${element.submitted_at}</td>
                    <td>${element.language}</td>
                    <td>${element.verdict}</td>
                `;
                queue_element.appendChild(submission);
            });

            console.log('Queue update:', data);
        }]
    ]
)
socket.emit('get_queue_data');
