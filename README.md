# 🚀 Optimizador de Prompts Inteligente 
(Proyecto grupal de alumnos de Samsung Innovation Campus) 

¡Bienvenido al **Optimizador de Prompts Inteligente**! Esta es una aplicación impulsada por Inteligencia Artificial (Llama-3 de Meta) y diseñada para transformar instrucciones básicas en prompts altamente profesionales, estructurados y listos para producción.

El sistema toma inspiración de las mejores prácticas de Prompt Engineering utilizadas por equipos avanzados (como Claude Code), asegurando que cada instrucción tenga contexto, reglas claras, delimitadores XML y separación de variables.

---

## ✨ Características Principales

1. **Optimizador Individual:** Ingresa una idea cruda (ej: "escribe un correo de disculpas") y el sistema la convertirá en un prompt estructurado usando etiquetas `<contexto>`, `<instrucciones>` y `<thinking>`, detectando automáticamente las variables necesarias como `{{NOMBRE_CLIENTE}}`.
2. **Procesamiento Masivo (Batch):** Sube un archivo `.csv` con docenas de instrucciones básicas y la aplicación generará una versión optimizada de cada una, devolviéndote un nuevo archivo listo para descargar.
3. **Historial Integrado:** Todas tus optimizaciones se guardan automáticamente en una base de datos local (Pandas) que puedes visualizar directamente en la interfaz.

---

## 🛠️ Tecnologías Utilizadas

- **Python 3**
- **Gradio:** Para el desarrollo de la interfaz de usuario web interactiva.
- **Pandas:** Para la gestión del historial y el procesamiento de lotes (archivos CSV).
- **Hugging Face Hub:** Para el consumo de la API de Inferencia conectada al modelo `Meta-Llama-3-8B-Instruct`.
- **Regex & XML Parsing:** Para la extracción de datos de manera resiliente frente a errores de generación del LLM.

---

## ⚙️ Instalación y Configuración Local

Sigue estos pasos para correr el proyecto en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/optimizador-de-prompts.git
cd optimizador-de-prompts
```

### 2. Crear un entorno virtual (Recomendado)
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar tu Token de Hugging Face
Para usar la IA, necesitas un token de acceso (gratuito) de Hugging Face.
1. Ve a [Hugging Face Settings -> Access Tokens](https://huggingface.co/settings/tokens) y crea un nuevo token (con permisos de lectura).
2. Renombra el archivo `.env.example` a `.env`.
3. Abre el archivo `.env` y pega tu token:
```env
HF_TOKEN="tu_token_aqui"
```

### 5. Iniciar la aplicación
```bash
python app.py
```
La aplicación se abrirá automáticamente en tu navegador en `http://127.0.0.1:7860`.

---

## 📁 Estructura del Proyecto

```text
optimizador-de-prompts/
│
├── data/                      # Carpeta de datos (historiales y resultados)
├── docs/                      # Documentación y reportes de pruebas
├── scripts/                   # Scripts secundarios y de validación
├── .env.example               # Plantilla de variables de entorno
├── .gitignore                 # Archivos ignorados por Git
├── app.py                     # Archivo principal de la aplicación
├── requirements.txt           # Dependencias de Python
└── README.md                  # Este archivo
```

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar el proyecto:
1. Haz un Fork del repositorio.
2. Crea tu rama de funcionalidad (`git checkout -b feature/MejorFeature`).
3. Haz commit a tus cambios (`git commit -m 'Agrega nueva feature'`).
4. Haz push a la rama (`git push origin feature/MejorFeature`).
5. Abre un Pull Request.

> _Proyecto desarrollado como demostración de integración de APIs de IA, Prompt Engineering y UX/UI con Gradio._
