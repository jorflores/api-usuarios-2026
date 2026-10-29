require('dotenv/config');

if (!process.env.DATABASE_URL || !process.env.JWT_SECRET) {
  console.error('Faltan variables de entorno: DATABASE_URL y JWT_SECRET (revisa tu .env)');
  process.exit(1);
}

const express = require('express');
const jwt = require('jsonwebtoken');
const prisma = require('./prisma');
const { SECRET, verificarToken, soloAdmin } = require('./middleware/auth');

const app = express();
const ROLES = ['admin', 'usuario'];

// ── Middleware global ───────────────────────────────────────────────
app.use(express.json()); // convierte el body JSON en req.body

app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`); // logger
  next();
});

// ── Rutas públicas ──────────────────────────────────────────────────
app.get('/', (req, res) => {
  res.json({ mensaje: 'API de usuarios funcionando' });
});

// POST /login  { correo, password }  ->  { token }
app.post('/login', async (req, res) => {
  const { correo, password } = req.body ?? {}; // sin body, Express 5 deja req.body como undefined
  if (!correo || !password) {
    return res.status(400).json({ error: 'Faltan correo o password' });
  }
  const usuario = await prisma.usuario.findUnique({
    where: { correo },
    omit: { password: false }, // aquí sí lo necesitamos, para compararlo
  });
  if (!usuario || usuario.password !== password) {
    return res.status(401).json({ error: 'No autorizado' });
  }
  const payload = { id: usuario.id, rol: usuario.rol };
  const token = jwt.sign(payload, SECRET, { expiresIn: '1h' });
  res.json({ token });
});

// ── De aquí para abajo, todo pide token ─────────────────────────────

// GET /perfil  ->  el usuario dueño del token
app.get('/perfil', verificarToken, async (req, res) => {
  const usuario = await prisma.usuario.findUnique({ where: { id: req.usuario.id } });
  if (!usuario) {
    return res.status(404).json({ error: 'No encontrado' });
  }
  res.json(usuario);
});

app.use('/usuarios', verificarToken);

// GET /usuarios  ->  todos
app.get('/usuarios', async (req, res) => {
  const usuarios = await prisma.usuario.findMany({ orderBy: { id: 'asc' } });
  res.json(usuarios);
});

// GET /usuarios/:id  ->  uno
app.get('/usuarios/:id', async (req, res) => {
  const usuario = await prisma.usuario.findUnique({
    where: { id: Number(req.params.id) },
  });
  if (!usuario) {
    return res.status(404).json({ error: 'No encontrado' });
  }
  res.json(usuario);
});

// POST /usuarios  { correo, password, rol? }  ->  201 + usuario  (solo admin)
app.post('/usuarios', soloAdmin, async (req, res) => {
  const { correo, password, rol } = req.body ?? {};
  if (!correo || !password) {
    return res.status(400).json({ error: 'Faltan datos' });
  }
  if (rol && !ROLES.includes(rol)) {
    return res.status(400).json({ error: 'Rol no válido' });
  }
  const nuevo = await prisma.usuario.create({
    data: { correo, password, rol },
  });
  res.status(201).json(nuevo);
});

// PUT /usuarios/:id  { correo, password, rol }  ->  usuario actualizado  (solo admin)
app.put('/usuarios/:id', soloAdmin, async (req, res) => {
  const id = Number(req.params.id);
  const existe = await prisma.usuario.findUnique({ where: { id } });
  if (!existe) {
    return res.status(404).json({ error: 'No encontrado' });
  }
  const { correo, password, rol } = req.body ?? {};
  if (rol && !ROLES.includes(rol)) {
    return res.status(400).json({ error: 'Rol no válido' });
  }
  const actualizado = await prisma.usuario.update({
    where: { id },
    data: { correo, password, rol },
  });
  res.json(actualizado);
});

// DELETE /usuarios/:id  ->  204 sin body  (solo admin)
app.delete('/usuarios/:id', soloAdmin, async (req, res) => {
  const id = Number(req.params.id);
  const existe = await prisma.usuario.findUnique({ where: { id } });
  if (!existe) {
    return res.status(404).json({ error: 'No encontrado' });
  }
  await prisma.usuario.delete({ where: { id } });
  res.status(204).send();
});

// ── Errores ─────────────────────────────────────────────────────────
// Express 5 manda aquí cualquier error de una ruta async.
app.use((err, req, res, next) => {
  if (err.code === 'P2002') {
    return res.status(409).json({ error: 'Ese correo ya está registrado' });
  }
  if (err.name === 'PrismaClientValidationError') {
    return res.status(400).json({ error: 'Datos no válidos' });
  }
  console.error(err);
  res.status(500).json({ error: 'Error interno' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`API en http://localhost:${PORT}`);
});
