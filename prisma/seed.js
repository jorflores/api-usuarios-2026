// Crea (o actualiza) el usuario admin inicial. Se puede correr varias veces.
require('dotenv/config');
const prisma = require('../src/prisma');

async function main() {
  const correo = process.env.ADMIN_CORREO || 'admin@mail.com';
  const password = process.env.ADMIN_PASSWORD || '1234';

  const admin = await prisma.usuario.upsert({
    where: { correo },
    update: { password, rol: 'admin' },
    create: { correo, password, rol: 'admin' },
  });
  console.log('Admin listo:', admin);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
