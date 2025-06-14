import { connectSocket } from './socketio.js';

const socket = connectSocket([
        ['queue_data', (data) => {
            let queue_element = document.getElementById('waiting-submissions');
            let judging_element = document.getElementById('judged-submissions');
            queue_element.innerHTML = '';
            judging_element.innerHTML = '';

            data["pending"].forEach(element => {
                const submission = document.createElement('tr');
                submission.innerHTML = `
                    <td>${element.problem_difficulty}</td>
                    <td>${element.problem_shortname}</td>
                    <td>${element.user_name}</td>
                    <td>${element.submitted_at}</td>
                    <td>${element.language}</td>
                    <td>${element.status}</td>
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
                    <td>${element.score}</td>
                    <td>${element.run_time}</td>
                `;
                if (element.score == 100) submission.className = 'verdict-success';
                else if (element.score == 0) submission.className = 'verdict-failure';
                else submission.className = 'verdict-partial';

                judging_element.appendChild(submission);
            });

            console.log(data["user_scores"]);
            let leaderboard = document.getElementById('leaderboard');
            leaderboard.innerHTML = '';

            data["user_scores"].forEach(([user_name,score]) => {
                const entry = document.createElement('li');
                entry.innerText = `${user_name}: ${score}`;
                leaderboard.appendChild(entry);
            });

            let refresh_counter = document.getElementById('refresh-counter');
            console.log(refresh_counter)
            console.log(data)
            if (data["token_refresh"] < 0) refresh_counter.innerHTML = 'At least one token available';
            else refresh_counter.innerHTML = `Time till refresh: ${data["token_refresh"]} seconds`;

            console.log('Queue update:', data);
        }]
    ]
)
socket.emit('get_queue_data');
