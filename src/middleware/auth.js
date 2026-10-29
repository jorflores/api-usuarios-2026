const jwt = require('jsonwebtoken');

const SECRET = process.env.JWT_SECRET;

// Revisa el gafete: ¿la petición trae un token válido?
function verificarToken(req, res, next) {
  const header = req.headers.authorization;
  if (!header) {
    return res.status(401).json({ error: 'Falta el token' });
  }
  const token = header.split(' ')[1]; // "Bearer eyJ..." -> "eyJ..."
  try {
    req.usuario = jwt.verify(token, SECRET); // { id, rol, iat, exp }
    next();
  } catch {
    res.status(401).json({ error: 'Token no válido' });
  }
}

// Va DESPUÉS de verificarToken: ya sabemos quién es, ¿puede hacerlo?
function soloAdmin(req, res, next) {
  if (req.usuario.rol !== 'admin') {
    return res.status(403).json({ error: 'Solo un admin puede hacer esto' });
  }
  next();
}

module.exports = { SECRET, verificarToken, soloAdmin };
