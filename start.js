const { spawn } = require('child_process');

const backend = spawn('node', ['path/to/backend.js']);
const frontend = spawn('electron', ['path/to/main.js']);

backend.on('exit', (code) => {
  console.error(`Backend process exited with code ${code}`);
  frontend.kill();
  process.exit(code);
});

frontend.on('exit', (code) => {
  console.error(`Frontend process exited with code ${code}`);
  backend.kill();
  process.exit(code);
});
