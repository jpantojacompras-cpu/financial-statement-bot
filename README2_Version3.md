# 🚀 Guía Completa: Cómo Subir tu Proyecto a GitHub

Este documento explica **paso a paso** cómo agregar todos tus archivos y carpetas a GitHub, para que tu proyecto sea accesible desde cualquier lugar.

---

## 📋 Tabla de Contenidos

- [Prerrequisitos](#-prerrequisitos)
- [Paso 1: Verifica tu estructura local](#-paso-1-verifica-tu-estructura-local)
- [Paso 2: Configura Git (primera vez)](#-paso-2-configura-git-primera-vez)
- [Paso 3: Agrega todos los archivos](#-paso-3-agrega-todos-los-archivos)
- [Paso 4: Haz un commit](#-paso-4-haz-un-commit)
- [Paso 5: Sube a GitHub](#-paso-5-sube-a-github)
- [Paso 6: Verifica en GitHub](#-paso-6-verifica-en-github)
- [Actualizaciones futuras](#-actualizaciones-futuras)
- [Troubleshooting](#-troubleshooting)

---

## ✅ Prerrequisitos

Antes de empezar, asegúrate de tener:

- ✅ **Git instalado** → Descargar desde [git-scm.com](https://git-scm.com/)
- ✅ **Cuenta de GitHub** → Crear en [github.com](https://github.com)
- ✅ **Repositorio creado** → Deberías tenerlo en https://github.com/tu-usuario/financial-statement-bot
- ✅ **Repositorio clonado localmente** → Carpeta `financial-statement-bot/` en tu computadora
- ✅ **Archivos creados** → Todas las carpetas y archivos del proyecto en tu máquina local

### Verifica que Git está instalado:

Abre una terminal y ejecuta:
```bash
git --version
```

Deberías ver algo como: `git version 2.40.0`

---

## 📂 Paso 1: Verifica tu estructura local

Primero, asegúrate de que TODOS tus archivos están en la carpeta correcta.

### Abre una terminal en la carpeta del proyecto:

```bash
cd financial-statement-bot
```

### Verifica la estructura con un comando:

**En Windows:**
```bash
tree /F
```

**En macOS/Linux:**
```bash
tree -L 3
```

**Alternativa (funciona en todos lados):**
```bash
ls -R
```

### Estructura esperada:

```
financial-statement-bot/
├── .git/                          (creado automáticamente)
├── .gitignore
├── LICENSE
├── README.md
├── README2.md
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── categories.csv
│   │   └── master_file.csv (se genera luego)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── movement.py
│   │   └── category.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── file_reader.py
│   │   ├── data_extractor.py
│   │   ├── normalizer.py
│   │   └── categorizer.py
│   ├── uploads/
│   └── venv/                      (no subir a GitHub)
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx
    │   ├── App.css
    │   ├── index.css
    │   └── components/
    │       ├── FileUploader.jsx
    │       ├── DataTable.jsx
    │       └── Dashboard.jsx
    ├── public/
    └── node_modules/              (no subir a GitHub)
```

✅ Si ves algo similar, ¡estás listo para el siguiente paso!

---

## 🔑 Paso 2: Configura Git (primera vez)

**SOLO SI ES LA PRIMERA VEZ** que usas Git en esta computadora.

### Abre una terminal y ejecuta:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tuemail@ejemplo.com"
```

**Ejemplo:**
```bash
git config --global user.name "jpantojacompras-cpu"
git config --global user.email "jpantoja@ejemplo.com"
```

### Verifica que se configuró correctamente:

```bash
git config --global user.name
git config --global user.email
```

Deberías ver tu nombre y email impresos.

---

## 📤 Paso 3: Agrega todos los archivos

Ahora agregaremos TODOS los archivos y carpetas a Git para que estén listos para subir.

### Comando principal:

```bash
git add .
```

**¿Qué hace?**
- Agrega TODOS los archivos nuevos y modificados a la "zona de staging"
- El punto `.` significa "todo en esta carpeta y subcarpetas"

### Verifica qué archivos se agregaron:

```bash
git status
```

Deberías ver algo como:

```
On branch main
Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   LICENSE
        new file:   README.md
        new file:   README2.md
        new file:   backend/main.py
        new file:   backend/requirements.txt
        new file:   backend/data/categories.csv
        new file:   backend/models/movement.py
        ...
        (muchos más archivos)
```

✅ Si ves tus archivos listados, ¡está correcto!

### (Opcional) Agregar archivos específicos:

Si prefieres ser más selectivo, puedes agregar solo ciertos archivos:

```bash
git add backend/
git add frontend/
git add README.md
git add .gitignore
```

### ⚠️ IMPORTANTE: Archivos que NO debes subir

Verifica que estas carpetas NO están en la lista:

```
backend/venv/           ❌ NO SUBIR
backend/uploads/        ❌ NO SUBIR (solo archivos temporales)
frontend/node_modules/  ❌ NO SUBIR
```

Si están ahí, es porque tu `.gitignore` no está bien. Verifica que contiene:

```
venv/
node_modules/
uploads/
*.csv (opcional, si no quieres subir datos)
```

---

## 📝 Paso 4: Haz un commit

Un commit es como una "foto" de tu proyecto en un momento específico. Es un punto en la historia de tu código.

### Ejecuta:

```bash
git commit -m "Agrega estructura inicial del proyecto con carpetas, módulos y archivos base"
```

**¿Qué es el `-m`?**
- `-m` significa "message" (mensaje)
- El texto entre comillas es una descripción de qué cambios hiciste
- Siempre usa presente: "Agrega", "Modifica", "Actualiza" (no "Agregado")

### Ejemplos de buenos mensajes:

```bash
git commit -m "Agrega módulo de lectura de archivos XLSX"
git commit -m "Implementa categorización automática"
git commit -m "Modifica estilos CSS del dashboard"
git commit -m "Corrige bug en extracción de movimientos"
```

### Ver historial de commits:

```bash
git log
```

Verás algo como:

```
commit a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Author: Tu Nombre <tuemail@ejemplo.com>
Date:   Wed Feb 25 10:30:00 2026 -0300

    Agrega estructura inicial del proyecto con carpetas, módulos y archivos base

commit q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5f6
Author: GitHub <noreply@github.com>
Date:   Wed Feb 25 10:00:00 2026 -0300

    Initial commit
```

---

## 🌐 Paso 5: Sube a GitHub

Ahora subes todos tus commits locales al repositorio en GitHub.

### Comando principal:

```bash
git push origin main
```

**¿Qué significa?**
- `git push` = "sube mis cambios"
- `origin` = "al repositorio remoto" (GitHub)
- `main` = "a la rama llamada main"

### Posibles respuestas:

#### ✅ Éxito (todo se subió):

```
Enumerating objects: 45, done.
Counting objects: 100% (45/45), done.
Delta compression using up to 8 threads.
Compressing objects: 100% (40/40), done.
Writing objects: 100% (45/45), 15.23 KiB | 2.50 MiB/s, done.
Total 45 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), done.
To https://github.com/tu-usuario/financial-statement-bot.git
   a1b2c3d..q1r2s3t  main -> main
```

#### ❌ Error de autenticación:

Si te pide credenciales, puedes hacer dos cosas:

**Opción 1: Token Personal (recomendado)**

1. Ve a https://github.com/settings/tokens
2. Haz click en "Generate new token (classic)"
3. Dale permisos `repo` y `gist`
4. Copia el token
5. Cuando Git te pida contraseña, pega el token

**Opción 2: SSH (más seguro pero más complejo)**

1. Genera claves SSH: `ssh-keygen -t ed25519 -C "tuemail@ejemplo.com"`
2. Agrega a GitHub en https://github.com/settings/keys
3. Usa URLs SSH en lugar de HTTPS

#### ❌ Rama no existe:

Si te dice "branch 'main' not found", tal vez tu rama se llama `master`:

```bash
git push origin master
```

O verifica qué rama tienes:

```bash
git branch
```

---

## 🔍 Paso 6: Verifica en GitHub

Ahora verificas que tu código está en GitHub viendo desde el navegador.

### 1. Abre tu navegador

Ve a:
```
https://github.com/tu-usuario/financial-statement-bot
```

**Ejemplo:**
```
https://github.com/jpantojacompras-cpu/financial-statement-bot
```

### 2. ¿Qué deberías ver?

- Todas tus **carpetas** listadas (backend/, frontend/)
- Todos tus **archivos** listados (main.py, requirements.txt, etc.)
- Un historial de commits a la derecha
- Tu archivo README.md mostrado debajo (si existe)

### 3. Explora tu repositorio

- **Haz click en cualquier carpeta** para ver su contenido
- **Haz click en cualquier archivo** para ver su código
- **Ve a "Code" → "Clone"** para copiar el link si alguien quiere clonar

### 4. Ejemplo visual:

```
📁 financial-statement-bot
├── 📄 README.md
├── 📄 README2.md
├── 📄 .gitignore
├── 📄 LICENSE
├── 📁 backend/
│   ├── 📄 main.py
│   ├── 📄 requirements.txt
│   ├── 📁 data/
│   ├── 📁 models/
│   └── 📁 modules/
└── 📁 frontend/
    ├── 📄 package.json
    ├── 📄 vite.config.js
    └── 📁 src/

🕐 Main branch | Last updated X minutes ago
```

✅ **¡Si ves todo esto, tu proyecto está en GitHub!**

---

## 🔄 Actualizaciones futuras

Cada vez que hagas cambios en tu proyecto local y quieras subirlos a GitHub:

### 1. Verifica qué cambió:
```bash
git status
```

### 2. Agrega los cambios:
```bash
git add .
```

### 3. Haz un commit:
```bash
git commit -m "Describe tu cambio aquí"
```

### 4. Sube a GitHub:
```bash
git push origin main
```

### Ejemplo real:

```bash
# Acabas de crear un nuevo archivo: backend/modules/utils.py

git status
# Output: modified:   backend/modules/utils.py

git add .
git commit -m "Agrega módulo de utilidades"
git push origin main

# ¡Listo! El archivo está en GitHub
```

---

## 🐛 Troubleshooting

### ❌ Problema: "fatal: not a git repository"

**Causa:** No estás dentro de una carpeta con Git inicializado.

**Solución:**
```bash
cd financial-statement-bot
```

O inicializa Git si no lo has hecho:
```bash
git init
```

---

### ❌ Problema: "Permission denied (publickey)"

**Causa:** Problemas de autenticación SSH.

**Solución:**
Cambia a HTTPS temporalmente:
```bash
git remote set-url origin https://github.com/tu-usuario/financial-statement-bot.git
git push origin main
```

---

### ❌ Problema: "Updates were rejected because the remote contains work that you do not have locally"

**Causa:** GitHub tiene cambios que tu máquina no tiene (ej: si editaste desde el navegador).

**Solución:**
```bash
git pull origin main
# Resuelve conflictos si los hay
git push origin main
```

---

### ❌ Problema: "fatal: The current branch main has no upstream branch"

**Causa:** Es la primera vez que subes la rama `main`.

**Solución:**
```bash
git push -u origin main
```

El `-u` configura la rama de rastreo automáticamente.

---

### ❌ Problema: No veo mis archivos en GitHub

**Causa:** Posibilidades:
1. El push no completó correctamente
2. Están en una rama diferente a `main`
3. Hay un error de autenticación silencioso

**Solución:**
```bash
# Verifica commits locales
git log

# Verifica la rama actual
git branch

# Verifica la conexión remota
git remote -v

# Intenta subir nuevamente
git push origin main
```

---

### ❌ Problema: Subí archivos que no debería (venv/, node_modules/, etc.)

**Causa:** El `.gitignore` no estaba bien configurado.

**Solución (opción rápida):**
```bash
# Desde GitHub web:
# 1. Ve a tu repositorio
# 2. Selecciona la carpeta (ej: node_modules/)
# 3. Haz click en los 3 puntos
# 4. Delete
# 5. Escribe un commit message
# 6. Commit

# Desde terminal (opción profesional):
git rm -r --cached venv/
git rm -r --cached node_modules/
git commit -m "Elimina carpetas excluidas del versionamiento"
git push origin main
```

---

### ❌ Problema: Accidentalmente incluí datos sensibles (.env, contraseñas, etc.)

**Causa:** Subiste archivos con información privada.

**Solución urgente:**
1. **NUNCA borres el archivo localmente** sin antes hacer backup
2. Desde GitHub, elimina el archivo manualmente
3. Actualiza tu `.gitignore`
4. **Considera cambiar contraseñas si están comprometidas**

```bash
# En terminal:
git rm --cached archivo_sensible.env
echo "archivo_sensible.env" >> .gitignore
git commit -m "Elimina archivo sensible y lo agrega a .gitignore"
git push origin main
```

---

## 🎯 Resumen Rápido

| Acción | Comando |
|--------|---------|
| Ver estado | `git status` |
| Agregar cambios | `git add .` |
| Hacer commit | `git commit -m "mensaje"` |
| Subir a GitHub | `git push origin main` |
| Bajarse cambios | `git pull origin main` |
| Ver historial | `git log` |
| Ver ramas | `git branch` |
| Cambiar rama | `git checkout nombre-rama` |

---

## 📚 Recursos Adicionales

- Documentación oficial de Git: https://git-scm.com/doc
- GitHub Hello World: https://guides.github.com/activities/hello-world/
- GitHub Docs: https://docs.github.com/en

---

## ✅ Checklist Final

Antes de considerar "completo" este proceso:

- [ ] Configuré Git con mi nombre y email
- [ ] Todos mis archivos están en la carpeta correcta
- [ ] Ejecuté `git add .`
- [ ] Hice `git commit` con un mensaje descriptivo
- [ ] Ejecuté `git push origin main`
- [ ] Entro a GitHub y veo todos mis archivos
- [ ] Puedo hacer click en carpetas y ver su contenido
- [ ] Puedo hacer click en archivos `.py`, `.jsx`, etc. y ver el código

✅ **¡Si todo está checkado, tu proyecto está correctamente en GitHub!**

---

**Última actualización:** 2026-02-25  
**Versión:** 1.0.0

> _Este documento es una guía práctica de Git y GitHub. Si tienes preguntas más avanzadas, consulta la documentación oficial._