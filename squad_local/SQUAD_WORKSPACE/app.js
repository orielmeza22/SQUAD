// Este archivo ahora será solo para el backend

const { createApp } = require('fastify');
const fastifyStatic = require('@fastify/static');
const path = require('path');

const app = createApp();

app.register(fastifyStatic, {
  root: path.join(__dirname, 'frontend'),
});

app.get('/', (request, reply) => {
  reply.sendFile('index.html');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, (err, address) => {
  if (err) {
    console.error(err);
    process.exit(1);
  }
  console.log(`Server listening at ${address}`);
});