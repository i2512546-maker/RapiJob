# RapiJob · Plataforma web

RapiJob es una aplicación web responsive para conectar clientes con técnicos profesionales en Huancayo, El Tambo y Chilca. La nueva aplicación reemplaza la interfaz anterior por una SPA construida con React y TypeScript.

## Tecnologías
- React 18 + TypeScript + Vite.
- Supabase Auth, PostgreSQL, Storage y Row Level Security (RLS).
- Google Maps JavaScript API para seleccionar ubicaciones y mostrar técnicos.
- FastAPI sirve el build web y entrega configuración pública en runtime.
- Docker multi-stage (Node para compilar y Python para servir).

## Funciones incluidas
- Acceso con correo y contraseña, registro de clientes y sesión persistente.
- Perfil personal editable y panel distinto según rol.
- Alta/promoción de técnicos restringida a administradores.
- Directorio de técnicos aprobados y disponibles desde Supabase.
- Solicitud de servicio con categoría, descripción, fecha/hora, dirección, coordenadas y fotos.
- Mapa con selección de ubicación y marcadores de técnicos disponibles.
- Panel cliente para consultar solicitudes y cancelar las pendientes.
- Panel técnico para consultar trabajos asignados, aceptar, marcar en camino, iniciar y completar.
- Administración para agregar un técnico a partir de una cuenta ya registrada.
- Categorías iniciales de los 12 rubros solicitados.

## Configuración obligatoria de Supabase

1. Crea un proyecto en https://supabase.com.
2. Abre **SQL Editor** y ejecuta el contenido completo de `supabase/schema.sql`.
3. En **Authentication → URL Configuration**, registra el dominio de producción y `http://localhost:5173` para desarrollo.
4. Crea tu cuenta de RapiJob desde la web.
5. En SQL Editor, convierte esa cuenta en administradora ejecutando:
   ```sql
   update public.profiles set role = 'admin' where email = 'TU_CORREO@EJEMPLO.COM';
   ```
   Sustituye el correo por el de tu cuenta. No existe un botón público para crear administradores.
6. En Supabase → Project Settings → API copia **Project URL** y **anon/public key**. Nunca uses ni publiques la clave `service_role`.

El SQL crea perfiles automáticamente al registrarse, las 12 categorías, tablas de solicitudes, perfiles técnicos, disponibilidad, reseñas, fotografías y políticas RLS. Los datos de clientes y solicitudes no son públicos. El directorio usa una vista que expone únicamente datos profesionales de técnicos aprobados y disponibles.

## Google Maps

En Google Cloud habilita **Maps JavaScript API** y **Geocoding API**. Crea una clave de navegador y restríngela por dominio HTTP y por APIs habilitadas. Configura esa clave como `GOOGLE_MAPS_API_KEY` en Render.

## Desplegar en Render

1. Conecta el repositorio `i2512546-maker/RapiJob` a Render usando el archivo `render.yaml`.
2. Render debe construir desde la raíz del repositorio (no establezcas `rootDir: backend`), porque Docker necesita leer también la carpeta `web`.
3. En el entorno del servicio añade:
   - `SUPABASE_URL`: URL de tu proyecto Supabase.
   - `SUPABASE_ANON_KEY`: clave anon/public de Supabase.
   - `GOOGLE_MAPS_API_KEY`: clave de Google Maps.
4. Despliega el último commit y comprueba `/health`.

La aplicación lee estas variables en cada inicio mediante `/config.json`, por lo que no se incrustan en el bundle durante la compilación. La clave anon de Supabase está diseñada para el navegador; RLS es obligatorio. Nunca configures `service_role` en el frontend.

## Ejecutar localmente

Requisitos: Node.js 20+ y Python 3.11+.

```bash
cd web
npm install
npm run dev
```

Para que el frontend local pueda leer la configuración, ejecuta también FastAPI en otro terminal con las variables `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `GOOGLE_MAPS_API_KEY` definidas, o usa Docker desde la raíz:

```bash
docker build -f backend/Dockerfile -t rapijob .
docker run --rm -p 10000:10000 \
  -e SUPABASE_URL=https://TU_PROYECTO.supabase.co \
  -e SUPABASE_ANON_KEY=TU_ANON_KEY \
  -e GOOGLE_MAPS_API_KEY=TU_MAPS_KEY rapijob
``

Abre `http://localhost:10000`.

## Reglas importantes
- Solo el administrador puede cambiar el rol de una cuenta y aprobar técnicos.
- Para agregar a un profesional, primero debe crear una cuenta normal; el administrador la busca por correo y la registra como técnico.
- No se inventan técnicos, calificaciones ni reseñas.
- La plataforma no procesa pagos ni almacena datos bancarios.
- Los estados se actualizan desde los controles del panel y se sincronizan mediante Supabase Realtime cuando la publicación está habilitada.
- El cliente puede dejar una calificación de 1 a 5 y un comentario al terminar el servicio.
- El técnico puede activar o pausar su perfil; la gestión de horarios semanales, notificaciones push, chat y pasarela de pagos siguen siendo ampliaciones pendientes.

## Seguridad
- Row Level Security está habilitado en las tablas principales.
- El SQL incluye protección para impedir que un usuario cambie su propio rol o apruebe su perfil técnico.
- Configura políticas y dominios de autenticación antes de abrir el servicio al público.
