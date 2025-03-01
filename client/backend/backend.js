const express = require('express');
const app = express();
const port = 3000;

// Basis-Route
app.get('/', (req, res) => {
  res.send('Hallo vom Backend!');
});

// Starte den Server
app.listen(port, () => {
  console.log(`Backend-Server läuft unter http://localhost:${port}`);
});
