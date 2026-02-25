# 📊 Financial Statement Bot
## Sistema Inteligente de Gestión de Cartolas Bancarias y Estados de Cuenta

[![Estado](https://img.shields.io/badge/estado-desarrollo-yellow)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue)]()
[![React](https://img.shields.io/badge/React-18+-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 📋 Tabla de Contenidos

- [Introducción](#-introducción)
- [Características Principales](#-características-principales)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Completa](#-instalación-completa)
- [Uso Paso a Paso](#-uso-paso-a-paso)
- [Formatos de Entrada](#-formatos-de-entrada-aceptados)
- [Estructura de Carpetas](#-estructura-de-carpetas)
- [Configuración de Categorías](#-configuración-de-categorías)
- [Dashboard y Visualización](#-dashboard-y-visualización)
- [Aprendizaje Automático](#-aprendizaje-automático-ml)
- [Exportación de Datos](#-exportación-de-datos)
- [Solución de Problemas](#-solución-de-problemas)
- [Preguntas Frecuentes](#-preguntas-frecuentes)
- [Contribuir](#-contribuir)

---

## 🎯 Introducción

**Financial Statement Bot** es una herramienta automatizada diseñada para ayudarte a gestionar tus finanzas personales o de tu PyME. Permite:

✅ Cargar cartolas bancarias en PDF y Excel  
✅ Extraer automáticamente movimientos (ingresos/gastos)  
✅ Categorizar y subcategorizar gastos inteligentemente  
✅ Consolidar toda la información en un archivo maestro  
✅ Visualizar dashboards con análisis mensual  
✅ Mejorar la precisión del sistema con tu feedback  

---

## ⚡ Características Principales

### 1. 📁 Lectura Multiformato
- Archivos `.xlsx` (Excel) con cartolas de bancos
- Archivos `.pdf` con estados de cuenta o cartolas
- Soporte para múltiples bancos simultáneamente

### 2. 🔍 Extracción Inteligente
- Detecta automáticamente: fecha, descripción, monto
- Clasifica movimientos como ingreso o gasto
- Mantiene referencia del archivo de origen

### 3. 🏷️ Categorización Automática
- Categorías y subcategorías personalizables
- Aprendizaje automático (ML) para mejorar precisión
- Correcciones manuales fáciles desde la UI

### 4. 📊 Dashboard Interactivo
- Resumen mensual de ingresos vs gastos
- Gráficos por categoría/subcategoría
- Filtros avanzados por fecha, banco, etc.

### 5. 💾 Consolidación de Datos
- Archivo maestro único con todos los movimientos
- Exportación en formato CSV
- Historial de carga y procesamiento

### 6. 🎨 Interfaz Amigable
- Drag & drop para cargar archivos
- Edición directa de categorías en la tabla
- Sin necesidad de conocimientos técnicos

---

## 🖥️ Requisitos Previos

Antes de instalar, asegúrate de tener:

- **Python 3.9+** ([Descargar](https://www.python.org/downloads/))
- **Node.js 16+** ([Descargar](https://nodejs.org/))
- **npm** (viene con Node.js)
- **pip** (administrador de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)

### Verificar instalación:
```bash
python --version  # Debe ser 3.9 o superior
node --version    # Debe ser 16 o superior
npm --version     # Debe estar instalado
```

---

## 📦 Instalación Completa

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/jpantojacompras-cpu/financial-statement-bot.git
cd financial-statement-bot
```

### Paso 2: Configurar el Backend

```bash
# Navegar a la carpeta del backend
cd backend

# Crear un entorno virtual (recomendado)
python -m venv venv

# Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar el Frontend

```bash
# Volver a la carpeta raíz
cd ../frontend

# Instalar dependencias de Node.js
npm install
```

### Paso 4: Crear carpetas necesarias

```bash
# Desde la raíz del proyecto
mkdir -p backend/uploads
mkdir -p backend/data
mkdir -p backend/models
```

### Paso 5: Configuración inicial de categorías

```bash
# Asegurar que existe el archivo de categorías
# (Verifica que `backend/data/categories.csv` existe)
```

---

## 🚀 Uso Paso a Paso

### 📍 Paso 1: Iniciar el Backend

Abre una terminal en la carpeta `backend` y ejecuta:

```bash
# Asegurate de estar en la carpeta backend y con el entorno virtual activado
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Esperado:** Verás un mensaje como:
```
Uvicorn running on http://127.0.0.1:8000
```

### 📍 Paso 2: Iniciar el Frontend

Abre **otra terminal** en la carpeta `frontend` y ejecuta:

```bash
npm run dev
```

**Esperado:** Verás:
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

### 📍 Paso 3: Acceder a la Aplicación

Abre tu navegador y ve a:
```
http://localhost:5173/
```

Deberías ver la interfaz principal con una sección de carga de archivos.

---

## 📄 Paso 4: Cargar tus Archivos

### Opción A: Drag & Drop

1. En la página principal, localiza la sección **"📁 Arrastra tus archivos"**
2. **Arrastra** tus archivos `.pdf` o `.xlsx` sobre el área indicada
3. Suelta los archivos

### Opción B: Click para seleccionar

1. Haz click en el área de carga
2. Selecciona uno o múltiples archivos de tu computadora
3. Confirma la selección

**Nota:** Puedes cargar varios archivos de diferentes bancos a la vez.

---

## 📍 Paso 5: Revisar y Editar Movimientos

Una vez cargados los archivos:

1. Los movimientos extraídos aparecerán en una **tabla**
2. Columnas visibles:
   - **Fecha:** Fecha del movimiento
   - **Descripción:** Detalle del movimiento
   - **Monto:** Cantidad movida
   - **Tipo:** Ingreso o Gasto
   - **Categoría:** Categoría asignada (editable)
   - **Subcategoría:** Subcategoría asignada (editable)
   - **Banco:** Banco de origen

### Editar Categorías Directamente:

- Haz **doble click** en la celda de categoría/subcategoría
- Se abrirá un dropdown o campo de texto
- Selecciona o escribe la categoría correcta
- Presiona **Enter** para guardar
- El sistema **aprenderá** de tus correcciones

---

## 📍 Paso 6: Procesar y Consolidar

Una vez revisados los movimientos:

1. Haz click en el botón **"✅ Procesar y Consolidar"**
2. El sistema validará todos los datos
3. Se creará el **archivo maestro** unificado

---

## 📍 Paso 7: Exportar Archivo Maestro

1. Haz click en **"⬇️ Descargar Archivo Maestro"**
2. Se descargará un archivo `.csv` con todos los movimientos consolidados
3. Este archivo contiene:
   - Todos los movimientos de todas las cartolas cargadas
   - Categorías y subcategorías asignadas
   - Información normalizada y lista para análisis

---

## 📍 Paso 8: Visualizar el Dashboard

1. Navega a la pestaña **"📊 Dashboard"**
2. Verás gráficos automáticamente generados:
   - **Gráfico de barras:** Ingresos vs Gastos por mes
   - **Gráfico de pastel:** Distribución de gastos por categoría
   - **Tabla de resumen:** Totales por categoría/subcategoría

3. Usa los filtros para:
   - Seleccionar rango de fechas
   - Filtrar por categoría
   - Filtrar por banco/archivo

---

## 📁 Formatos de Entrada Aceptados

### 📊 Archivos Excel (.xlsx)

Estructura esperada (puede variar según el banco):

```
| Fecha      | Descripción                    | Monto     |
|------------|--------------------------------|-----------|
| 2024-01-15 | Salario Enero                  | 3000.00   |
| 2024-01-16 | Supermercado TuCasa            | -150.00   |
| 2024-01-18 | Netflix Suscripción            | -15.99    |
| 2024-01-20 | Transferencia Recibida         | 500.00    |
```

**Requisitos:**
- Una columna con fecha (puede llamarse "Fecha", "Date", "Fecha_movimiento", etc.)
- Una columna con descripción (puede llamarse "Descripción", "Concepto", "Description", etc.)
- Una columna con monto (puede llamarse "Monto", "Amount", "Cantidad", etc.)
- Montos negativos = gastos; positivos = ingresos

### 📄 Archivos PDF (.pdf)

- Cartolas en formato tabla (no escaneadas como imagen)
- El sistema trata de detectar automáticamente la tabla de movimientos
- Si el PDF tiene múltiples tablas, procesará todas

**Consejo:** Si tu banco proporciona PDF escaneado (imagen), convierte a Excel primero usando:
- Herramientas online como [Smallpdf](https://smallpdf.com/)
- Software local como [Tabula](https://tabula.technology/)

---

## 📂 Estructura de Carpetas

```
financial-statement-bot/
│
├── backend/
│   ├── main.py                    # Aplicación principal FastAPI
│   ├── requirements.txt           # Dependencias Python
│   ├── modules/
│   │   ├── file_reader.py         # Lectura de PDF/XLSX
│   │   ├── data_extractor.py      # Extracción de movimientos
│   │   ├── normalizer.py          # Normalización de datos
│   │   └── categorizer.py         # Categorización inteligente
│   ├── models/
│   │   ├── movement.py            # Modelo de movimiento
│   │   └── category.py            # Modelo de categoría
│   ├── data/
│   │   ├── categories.csv         # Categorías base
│   │   └── master_file.csv        # Archivo maestro (generado)
│   ├── models/
│   │   └── categorizer.pkl        # Modelo ML guardado
│   └── uploads/                   # Archivos temporales subidos
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUploader.jsx   # Carga de archivos
│   │   │   ├── DataTable.jsx      # Tabla de movimientos
│   │   │   ├── Dashboard.jsx      # Dashboard de visualización
│   │   │   └── CategoryEditor.jsx # Edición de categorías
│   │   ├── App.jsx                # Componente principal
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   └── GUIA_USUARIOS.md           # Guía detallada para usuarios
│
├── .gitignore
├── README.md                      # Este archivo
└── docker-compose.yml             # (Opcional) Para despliegue

```

---

## 🏷️ Configuración de Categorías

### Archivo de Categorías (`categories.csv`)

Localización: `backend/data/categories.csv`

**Estructura esperada:**

```csv
categoria,subcategoria,keywords
Alimentación,Supermercado,"Taco, Supermarket, Walmart, Carrefour, Unimarc"
Alimentación,Restaurantes,"Restaurant, Dominos, McDonald's, Pizzería"
Transporte,Combustible,"Shell, Copec, Esso, Gasolina"
Transporte,Taxi,"Uber, Cabify, Didi, Taxi"
Servicios,Telecom,"Movistar, Entel, Claro, Internet"
Servicios,Electricidad,"Enel, Luz, Energía"
Salud,Farmacia,"Farmacias Ahumada, Cruz Azul"
Salud,Médico,"Clínica, Doctor, Consultorio"
Vivienda,Arriendo,"Arriendo, Rent"
Vivienda,Servicios,"Agua, Alcantarillado"
```

### Cómo Agregar Nuevas Categorías:

1. **Opción A (Manual):**
   - Abre `backend/data/categories.csv`
   - Agrega una línea nueva con tu categoría/subcategoría
   - Agrégale palabras clave separadas por comas

2. **Opción B (Desde la UI):**
   - En el dashboard, hay un botón "⚙️ Gestionar Categorías"
   - Agrega nueva categoría/subcategoría
   - Guarda los cambios

### Cómo Funciona el Matching:

El sistema busca coincidencias entre las palabras clave del `.csv` y la descripción del movimiento.

**Ejemplo:**
```
Descripción: "WALMART SUPERMERCADO 2024"
Busca: "Walmart" en keywords
Encuentra: Categoría=Alimentación, Subcategoría=Supermercado
```

---

## 📊 Dashboard y Visualización

### Vista General

Una vez tengas datos procesados, ve a la pestaña **"Dashboard"** para ver:

#### 1. Gráfico de Ingresos vs Gastos Mensual
```
Ingresos/Gastos por Mes
─────────────────────
3000│ ▁▂▃▅▇█▇▅▃▂▁
2000│ ▄▅▆▇█▇▆▅▄▃▂
1000│ ▅▆▇▇█▇▆▅▄▃▂
   0│ ──────────────
     Ene Feb Mar Abr May Jun...
     
   Azul: Ingresos | Rojo: Gastos
```

#### 2. Distribución de Gastos por Categoría
```
Gráfico de Pastel:
- Alimentación: 35%
- Transporte: 20%
- Servicios: 25%
- Salud: 10%
- Otros: 10%
```

#### 3. Tabla de Resumen
```
| Categoría      | Subcategoría    | Total Mes | % del Total |
|----------------|-----------------|-----------|-------------|
| Alimentación   | Supermercado    | $2,500    | 28%         |
| Transporte     | Combustible     | $1,200    | 13%         |
| Servicios      | Telecom         | $800      | 9%          |
| ...            | ...             | ...       | ...         |
```

### Filtros Disponibles

- **Rango de Fechas:** Desde y Hasta (mes/año)
- **Categoría:** Selecciona una o todas
- **Subcategoría:** Filtra dentro de la categoría
- **Banco:** Por archivo/banco de origen
- **Tipo:** Solo ingresos, solo gastos, o ambos

### Acciones desde el Dashboard

- **Descargar gráfico:** Click derecho → Guardar imagen
- **Descargar datos:** Botón "⬇️ Exportar como CSV"
- **Ver detalle:** Haz click en una categoría del gráfico de pastel

---

## 🤖 Aprendizaje Automático (ML)

### ¿Cómo Aprende el Sistema?

1. **Primera carga:** El sistema usa coincidencias simples de palabras clave del `categories.csv`
2. **Correcciones manuales:** Cuando corriges una categoría, el sistema registra esa corrección
3. **Entrenamiento:** Tras acumular correcciones, entrena un modelo de Machine Learning
4. **Predicción futura:** Los próximos movimientos similares se categorían más precisamente

### Procesos Automáticos

El sistema se actualiza automáticamente cuando:

- ✅ Corriges una categoría en la tabla
- ✅ Haces click en "✅ Procesar y Consolidar"
- ✅ Se descarga el archivo maestro

### Ver el Estado del Aprendizaje

En la UI, verás un indicador:
```
🧠 Modelo ML: Entrenado (Precisión: 87%)
```

Mientras más correcciones hagas, mayor será la precisión.

---

## 💾 Exportación de Datos

### Archivo Maestro CSV

**Ubicación:** `backend/data/master_file.csv`

**Contenido:**
```csv
fecha,descripcion,monto,tipo,categoria,subcategoria,archivo_referencia,banco
2024-01-15,Salario Enero,3000.00,ingreso,Ingresos,Salario,cartola_enero.xlsx,Banco A
2024-01-16,Walmart Supermercado,-150.00,gasto,Alimentación,Supermercado,cartola_enero.xlsx,Banco A
2024-01-18,Netflix Suscripción,-15.99,gasto,Entretenimiento,Suscripciones,estado_tc.pdf,Tarjeta Crédito
```

### Cómo Descargar

1. En la UI, haz click en **"⬇️ Descargar Archivo Maestro"**
2. Se descargará automáticamente como `master_file_[fecha].csv`
3. Ábrelo en Excel, Google Sheets o tu herramienta favorita

### Usos del Archivo Maestro

- 📊 Análisis en Excel/Google Sheets
- 📈 Importar a software contable
- 💹 Análisis avanzado con Python/R
- 📱 Importar a apps de finanzas personales

---

## 🆘 Solución de Problemas

### ❌ Error: "No se pudo leer el archivo PDF"

**Causa:** El PDF es un escaneo (imagen) o tiene formato no estándar.

**Solución:**
1. Intenta convertir el PDF a Excel usando [Smallpdf](https://smallpdf.com/)
2. O descarga la cartola nuevamente de tu banco en formato Excel
3. Si el PDF es text-based, intenta abrir con Tabula:
   - Descarga [Tabula](https://tabula.technology/)
   - Abre tu PDF
   - Selecciona la tabla y extrae

### ❌ Error: "Las columnas no coinciden"

**Causa:** El archivo Excel tiene nombres de columnas diferentes.

**Solución:**
1. Abre el archivo Excel
2. Renombra las columnas a estándares:
   - Fecha → `Fecha`
   - Descripción → `Descripción`
   - Monto → `Monto`
3. Guarda y recarga el archivo

### ❌ Error: "El backend no responde"

**Causa:** El servidor backend no está ejecutándose.

**Solución:**
1. Abre una terminal
2. Navega a `backend/`
3. Ejecuta: `uvicorn main:app --reload`
4. Verifica que ves: `Uvicorn running on http://127.0.0.1:8000`

### ❌ Error: "El frontend no carga"

**Causa:** El servidor frontend no está ejecutándose.

**Solución:**
1. Abre otra terminal
2. Navega a `frontend/`
3. Ejecuta: `npm run dev`
4. Accede a `http://localhost:5173``
