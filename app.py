import gradio as gr
import json
import re
import pandas as pd
import os
import time
from huggingface_hub import InferenceClient
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Token de Hugging Face (ahora seguro usando .env)
HF_TOKEN = os.getenv("HF_TOKEN")
client = InferenceClient(token=HF_TOKEN, timeout=60)

# Archivos de datos reubicados en la carpeta data/
os.makedirs("data", exist_ok=True)
HISTORIAL_FILE = os.path.join("data", "historial_prompts.csv")

def guardar_historial(original, contexto, tono, optimizado, variables, explicacion):
    """Guarda el registro de la optimización en un CSV usando Pandas."""
    nuevo_registro = pd.DataFrame([{
        "Prompt Original": original,
        "Contexto": contexto,
        "Tono": tono,
        "Prompt Optimizado": optimizado,
        "Variables": variables,
        "Explicación": explicacion
    }])
    
    if os.path.exists(HISTORIAL_FILE):
        nuevo_registro.to_csv(HISTORIAL_FILE, mode='a', header=False, index=False, encoding='utf-8')
    else:
        nuevo_registro.to_csv(HISTORIAL_FILE, index=False, encoding='utf-8')

def leer_historial():
    """Lee el historial actual para mostrarlo en el DataFrame."""
    if os.path.exists(HISTORIAL_FILE):
        try:
            df = pd.read_csv(HISTORIAL_FILE)
            # Retorna solo los últimos 100 registros (invertidos) para evitar Out of Memory en la interfaz
            return df.tail(100).iloc[::-1]
        except Exception:
            pass
    return pd.DataFrame(columns=["Prompt Original", "Contexto", "Tono", "Prompt Optimizado", "Variables", "Explicación"])

def obtener_archivos_historial():
    """Devuelve las rutas del historial en CSV y Markdown (.md)."""
    archivos = []
    if os.path.exists(HISTORIAL_FILE):
        df = pd.read_csv(HISTORIAL_FILE)
        
        # Generar CSV de exportación formateado como tabla para Excel (separador ';' y UTF-8 con BOM)
        # Reordenamos para que 'Prompt Optimizado' sea la primera columna para futuras optimizaciones por lote
        csv_export_path = os.path.join("data", "historial_prompts_tabla.csv")
        cols = ['Prompt Optimizado', 'Prompt Original', 'Contexto', 'Tono', 'Variables', 'Explicación']
        cols_existentes = [c for c in cols if c in df.columns]
        export_df = df[cols_existentes]
        export_df.to_csv(csv_export_path, index=False, sep=';', encoding='utf-8-sig')
        archivos.append(csv_export_path)
        
        # Generar versión Markdown para copiar y pegar fácilmente
        md_path = os.path.join("data", "historial_prompts.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# 🗂️ Historial de Prompts Optimizados\n\n")
            for index, row in df.iterrows():
                f.write(f"## Idea Original: {row['Prompt Original']}\n\n")
                if pd.notna(row.get('Contexto')) and str(row['Contexto']).strip():
                    f.write(f"**Contexto:** {row['Contexto']}\n\n")
                if pd.notna(row.get('Tono')) and str(row['Tono']).strip():
                    f.write(f"**Tono:** {row['Tono']}\n\n")
                f.write(f"### ✨ Prompt Optimizado\n```text\n{row['Prompt Optimizado']}\n```\n\n")
                vars_detectadas = str(row.get('Variables', ''))
                if pd.isna(row.get('Variables')) or vars_detectadas.strip().lower() == 'nan':
                    vars_detectadas = "Ninguna"
                f.write(f"**Variables:** {vars_detectadas}\n\n")
                f.write(f"**Explicación:** {row.get('Explicación', '')}\n\n")
                f.write("---\n\n")
        archivos.append(md_path)
        
    return archivos if archivos else None

def optimizar_prompt(prompt_original, contexto, tono, progress=gr.Progress()):
    """Función que optimiza prompts basándose en las mejores prácticas de Claude."""
    intentos_maximos = 3
    if not prompt_original or not str(prompt_original).strip():
        return "Por favor, ingresa un prompt original.", "", "No se ingresó texto."
        
    progress(0, desc="Preparando sistema e instrucciones...")
    system_prompt = """Eres un experto en Prompt Engineering inspirado en las mejores prácticas de Anthropic (Claude).
Tu objetivo es transformar instrucciones básicas en prompts altamente estructurados, profesionales y efectivos.

REGLAS ESTRICTAS PARA EL PROMPT GENERADO:
1. Organiza claramente las secciones usando párrafos limpios separados por saltos de línea. NO utilices etiquetas XML internas (como <contexto> o <instrucciones>) dentro del prompt optimizado.
2. Si la tarea requiere datos de entrada del usuario final, define variables usando dobles llaves, ej: {{NOMBRE_VARIABLE}}.
3. Instruye explícitamente al modelo a analizar y pensar paso a paso su estructura lógica antes de dar la respuesta final.
4. Asigna un rol claro al modelo (ej. "Eres un experto en...").
5. Integra instrucciones de comunicación efectiva: pide al modelo que cuide la claridad del mensaje, la apertura, y se adapte a su audiencia.

DEBES responder ÚNICAMENTE usando las siguientes etiquetas XML:
<resultado>
  <prompt_optimizado>El texto completo del prompt final aquí (sin etiquetas XML en su interior)...</prompt_optimizado>
  <variables>VARIABLE_1, VARIABLE_2</variables>
  <explicacion>Breve explicación de las técnicas utilizadas.</explicacion>
</resultado>

--- EJEMPLO DE RESPUESTA ESPERADA ---
<resultado>
  <prompt_optimizado>Eres un especialista en atención al cliente.

Contexto:
El cliente {{NOMBRE_CLIENTE}} está molesto por un retraso en la entrega de su pedido.

Instrucciones:
Redacta un correo de disculpa empático que ofrezca una solución rápida y opciones de compensación.

Piensa paso a paso sobre el tono adecuado antes de redactar la respuesta final.</prompt_optimizado>
  <variables>NOMBRE_CLIENTE</variables>
  <explicacion>Se asignó un rol, se usaron párrafos limpios sin etiquetas XML y se extrajo la variable NOMBRE_CLIENTE.</explicacion>
</resultado>
"""

    user_message = f"Optimiza el siguiente prompt:\n<PROMPT_ORIGINAL>\n{prompt_original}\n</PROMPT_ORIGINAL>\n"
    if contexto.strip():
        user_message += f"\nContexto adicional: {contexto}"
    if tono:
        user_message += f"\nTono deseado: {tono}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    for intento in range(intentos_maximos):
        progress((intento, intentos_maximos), desc=f"Llamando a Llama-3 (Intento {intento + 1}/{intentos_maximos})...")
        try:
            response = client.chat_completion(
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                messages=messages,
                max_tokens=1024,
                temperature=0.7
            )
            
            progress(0.9, desc="Analizando respuesta del modelo...")
            full_response = response.choices[0].message["content"]
            
            prompt_match = re.search(r'<prompt_optimizado>([\s\S]*?)</prompt_optimizado>', full_response, re.IGNORECASE)
            variables_match = re.search(r'<variables>([\s\S]*?)</variables>', full_response, re.IGNORECASE)
            explicacion_match = re.search(r'<explicaci[oó]n>([\s\S]*?)</explicaci[oó]n>', full_response, re.IGNORECASE)
            
            if prompt_match and explicacion_match:
                optimizado = prompt_match.group(1).strip()
                explicacion = explicacion_match.group(1).strip()
                variables = variables_match.group(1).strip() if variables_match else ""
                guardar_historial(prompt_original, contexto, tono, optimizado, variables, explicacion)
                return optimizado, variables, explicacion
            else:
                error_msg = "Tu respuesta no contiene las etiquetas XML requeridas (<prompt_optimizado> y <explicacion> o <explicación>). Asegúrate de envolver tu respuesta en la etiqueta <resultado>. REINTENTA AHORA."
                messages.append({"role": "assistant", "content": full_response})
                messages.append({"role": "user", "content": error_msg})
                
        except Exception as e:
            if intento == intentos_maximos - 1:
                return f"Error crítico tras {intentos_maximos} intentos:\n{str(e)}", "", "Fallo de comunicación con la IA."
            time.sleep(2) # Espera antes de reintentar para evitar bloqueos por red
            
    return f"Error: No se pudo generar el XML. Esto respondió el modelo:\n\n{full_response}", "", "El modelo no respetó el formato XML."

def procesar_batch(file, progress=gr.Progress()):
    """Procesa un CSV entero iterando fila por fila usando Pandas."""
    if file is None:
        return None, "Por favor, sube un archivo CSV."
    
    try:
        # Usar engine='python' y sep=None para autodetectar separadores (, o ;)
        df = pd.read_csv(file.name, sep=None, engine='python')
        
        # Validar existencia de la columna Prompt (o usar la primera)
        if 'Prompt' not in df.columns:
            df.rename(columns={df.columns[0]: 'Prompt'}, inplace=True)
            
        resultados_optimizados = []
        variables_list = []
        explicaciones = []
        
        total_rows = len(df)
        
        # Prevenir Out of Memory y Timeouts limitando el tamaño del lote
        if total_rows > 500:
            return None, f"Error: El archivo tiene {total_rows} filas. El límite máximo para evitar caídas de memoria o red es de 500 filas."
        
        # Iterar cada fila y optimizar
        for index, row in df.iterrows():
            progress((index, total_rows), desc=f"Optimizando Prompt {index + 1} de {total_rows}")
            if pd.isna(row['Prompt']) or not str(row['Prompt']).strip() or str(row['Prompt']).strip().lower() == "nan":
                resultados_optimizados.append("Fila ignorada (vacía)")
                variables_list.append("")
                explicaciones.append("No se procesó porque el prompt estaba vacío.")
                continue
                
            prompt = str(row['Prompt'])
            contexto = str(row['Contexto']) if 'Contexto' in df.columns and pd.notna(row['Contexto']) else ""
            tono = str(row['Tono']) if 'Tono' in df.columns and pd.notna(row['Tono']) else ""
            
            opt, var, exp = optimizar_prompt(prompt, contexto, tono)
            resultados_optimizados.append(opt)
            variables_list.append(var)
            explicaciones.append(exp)
            
        # Añadir las nuevas columnas al Dataframe
        df['Prompt Optimizado'] = resultados_optimizados
        df['Variables Detectadas'] = variables_list
        df['Explicación'] = explicaciones
        
        # Guardar archivo procesado en carpeta data/
        output_path_csv = os.path.join("data", "prompts_optimizados_batch.csv")
        df.to_csv(output_path_csv, index=False, encoding='utf-8')
        
        # Generar versión Markdown para leer y copiar fácilmente
        output_path_md = os.path.join("data", "prompts_optimizados_batch.md")
        with open(output_path_md, "w", encoding="utf-8") as f:
            f.write("# 🚀 Resultados del Procesamiento por Lotes\n\n")
            for index, row in df.iterrows():
                f.write(f"## Idea Original: {row['Prompt']}\n\n")
                if pd.notna(row.get('Contexto')) and str(row['Contexto']).strip():
                    f.write(f"**Contexto:** {row['Contexto']}\n\n")
                if pd.notna(row.get('Tono')) and str(row['Tono']).strip():
                    f.write(f"**Tono:** {row['Tono']}\n\n")
                f.write(f"### ✨ Prompt Optimizado\n```text\n{row.get('Prompt Optimizado', '')}\n```\n\n")
                vars_detectadas = str(row.get('Variables Detectadas', ''))
                if pd.isna(row.get('Variables Detectadas')) or vars_detectadas.strip().lower() == 'nan':
                    vars_detectadas = "Ninguna"
                f.write(f"**Variables:** {vars_detectadas}\n\n")
                f.write(f"**Explicación:** {row.get('Explicación', '')}\n\n")
                f.write("---\n\n")
        
        return [output_path_csv, output_path_md], "¡Procesamiento por lotes completado con éxito!"
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

# Definición del Tema AI Startup
ai_startup_theme = gr.themes.Default(
    primary_hue="green",
    secondary_hue="emerald",
    neutral_hue="slate",
    font=(gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"),
).set(
    body_background_fill="#000000",
    body_text_color="#FFFFFF",
    background_fill_primary="#0A0A0A",
    background_fill_secondary="#111111",
    border_color_accent="#00FF41",
    border_color_primary="#333333",
    color_accent_soft="#003B00",
    block_background_fill="#0A0A0A",
    block_label_text_color="#00FF41",
    button_primary_background_fill="#00FF41",
    button_primary_text_color="#000000",
    button_primary_border_color="#00FF41",
    button_secondary_background_fill="#111111",
    button_secondary_text_color="#FFFFFF",
)

css = """
body, .gradio-container { background-color: #000000 !important; }
button.primary { transition: all 0.3s ease; border-radius: 8px !important; box-shadow: 0 4px 10px rgba(0, 255, 65, 0.4) !important; font-weight: bold; }
button.primary:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0, 255, 65, 0.6) !important; background-color: #00FF41 !important; color: #000000 !important; }
.hero-title { text-align: center; color: #00FF41; font-size: 2.8em; margin-bottom: 0.2em; font-weight: 800; letter-spacing: -0.02em; text-shadow: 0 0 10px rgba(0, 255, 65, 0.5); }
.hero-subtitle { text-align: center; color: #FFFFFF; font-size: 1.2em; font-weight: 400; margin-bottom: 2em; }
.feature-card { background-color: #0A0A0A; border: 1px solid #00FF41; border-radius: 12px; padding: 24px; margin-top: 2em; box-shadow: 0 4px 15px rgba(0, 255, 65, 0.1); max-width: 600px; margin-left: auto; margin-right: auto; }
.feature-card h3 { color: #00FF41; margin-top: 0; text-shadow: 0 0 5px rgba(0, 255, 65, 0.4); }
.feature-card p { color: #FFFFFF !important; }
.tabs { background-color: #000000; border-bottom: 1px solid #333333 !important; }

/* FIX DE CONSTRASTE PARA CAJAS DE TEXTO Y TABLAS EN MODO CLARO */
.gradio-container textarea, .gradio-container input, .gradio-container select { 
    background-color: #0A0A0A !important; 
    color: #00FF41 !important; 
    border: 1px solid #333333 !important; 
}
.table-wrap, .table-wrap table, .table-wrap th, .table-wrap td, .table-wrap tr, .table-wrap span, tbody, thead {
    background-color: #0A0A0A !important;
    color: #FFFFFF !important;
    border-color: #333333 !important;
}
.table-wrap tr:nth-child(even) td { background-color: #111111 !important; }

/* FIXES POR PETICIÓN DEL USUARIO */
.gradio-container code, .gradio-container kbd, .prose code {
    color: #008F11 !important;
    background-color: transparent !important;
    font-weight: 800 !important;
    border: none !important;
}

/* Forzar que CADA FILA del Visor de Archivos o Tablas sea OSCURA siempre, y su letra clara */
.gradio-container .file-preview, .gradio-container .file-preview tbody, .gradio-container table {
    background-color: #0A0A0A !important;
    border-color: #333333 !important;
}
.gradio-container tr, .gradio-container td, .gradio-container th, .gradio-container tr.file, .gradio-container a.file, .gradio-container tr.file span {
    background-color: #0A0A0A !important;
    color: #FFFFFF !important;
    border-color: #333333 !important;
}
.gradio-container tr:nth-child(even) td, .gradio-container tr:nth-child(even) span, .gradio-container tr:nth-child(even) a { 
    background-color: #111111 !important; 
    color: #FFFFFF !important;
}

.gradio-container .wrap, .gradio-container fieldset {
    border: 2px solid #00FF41 !important;
}

/* Ocultar por completo la configuración de Tema de Gradio y el footer */
footer { display: none !important; }
.theme-toggle, .dark-mode-toggle, .gradio-settings { display: none !important; }
"""

# Forzar a Gradio a activar su modo oscuro nativo para elementos complejos (Dropdowns, uploaders)
js_code = """
function force_dark_mode() {
    document.body.classList.add('dark');
    localStorage.setItem("theme", "dark");
}
"""

# Diseño de la Interfaz con Gradio Blocks
with gr.Blocks() as demo:
    
    with gr.Tabs():
        # PESTAÑA 1: LANDING PAGE
        with gr.Tab("🏠 Inicio"):
            gr.Markdown("<br>")
            gr.Markdown("<h1 class='hero-title'>Optimizador de Prompts v2.0</h1>")
            gr.Markdown("<p class='hero-subtitle'>Eleva tus instrucciones al nivel de un Prompt Engineer profesional, impulsado por Llama 3.</p>")
            gr.Markdown(
                """
                <div class="feature-card">
                    <h3>🚀 Potencia tu IA</h3>
                    <p style="margin-bottom: 15px;">Esta herramienta transforma instrucciones básicas en <b>prompts altamente estructurados</b>. Utilizamos técnicas avanzadas de inyección de contexto, roles explícitos y delimitadores XML.</p>
                    <p style="color: #9CA3AF; font-size: 0.9em;"><i>Selecciona una de las pestañas superiores para comenzar la optimización individual o cargar tus archivos en lote.</i></p>
                </div>
                """
            )
            gr.Markdown("<br><br>")
        
        # PESTAÑA 2: OPTIMIZADOR INDIVIDUAL
        with gr.Tab("👤 Optimización Individual"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 1. Parámetros de Entrada")
                    prompt_original = gr.Textbox(label="Prompt Original", placeholder="Ej. Escribe un post sobre inteligencia artificial...", lines=4)
                    contexto = gr.Textbox(label="Contexto Adicional (Opcional)", placeholder="Ej. Es para LinkedIn, dirigido a programadores junior.", lines=2)
                    tono = gr.Dropdown(choices=["Profesional", "Casual", "Creativo", "Humorístico", "Académico", "Persuasivo", "Directo"], label="Tono de la respuesta", value="Profesional")
                    btn_optimizar = gr.Button("✨ Optimizar Prompt", variant="primary", size="lg")
                    btn_reoptimizar = gr.Button("🔄 Optimizar Más (Usar resultado actual)", variant="secondary", size="sm")
                    
                with gr.Column(scale=1):
                    with gr.Row():
                        gr.Markdown("### 2. Resultado Estructurado")
                        btn_copiar = gr.Button("📋 Copiar Prompt", size="sm")
                    prompt_optimizado = gr.Textbox(label="Prompt Final Optimizado", lines=7, interactive=False)
                    variables_detectadas = gr.Textbox(label="Variables Detectadas", lines=1)
                    explicacion = gr.Textbox(label="Técnicas Aplicadas", lines=3)
                    
            btn_optimizar.click(fn=optimizar_prompt, inputs=[prompt_original, contexto, tono], outputs=[prompt_optimizado, variables_detectadas, explicacion])
            btn_reoptimizar.click(fn=optimizar_prompt, inputs=[prompt_optimizado, contexto, tono], outputs=[prompt_optimizado, variables_detectadas, explicacion])
            btn_copiar.click(fn=None, inputs=[prompt_optimizado], outputs=None, js="(text) => { navigator.clipboard.writeText(text); return []; }")
        
        # PESTAÑA 3: BATCH
        with gr.Tab("📊 Procesamiento Masivo"):
            gr.Markdown("### Operaciones en Lote (Batch)")
            gr.Markdown("Procesa múltiples ideas simultáneamente subiendo un archivo CSV con una columna `Prompt` (y opcionalmente `Contexto` y `Tono`).")
            
            with gr.Row():
                with gr.Column():
                    archivo_entrada = gr.File(label="1. Subir archivo CSV de entrada", file_types=[".csv"])
                    btn_batch = gr.Button("🚀 Iniciar Procesamiento", variant="primary")
                    estado_batch = gr.Textbox(label="Estado del procesamiento", interactive=False)
                with gr.Column():
                    archivo_salida = gr.File(label="2. Descargar Resultados (CSV y Markdown)", file_count="multiple")
                    
            btn_batch.click(fn=procesar_batch, inputs=[archivo_entrada], outputs=[archivo_salida, estado_batch])

        # PESTAÑA 4: HISTORIAL
        with gr.Tab("🗂️ Historial Local"):
            gr.Markdown("### Base de Datos de Optimizaciones")
            
            with gr.Row():
                btn_actualizar_historial = gr.Button("🔄 Actualizar Registros", size="sm")
                archivo_historial = gr.File(label="Exportar Logs", file_count="multiple")
                
            tabla_historial = gr.Dataframe(value=leer_historial, interactive=False, wrap=True)
            
            btn_actualizar_historial.click(fn=leer_historial, outputs=tabla_historial)
            btn_actualizar_historial.click(fn=obtener_archivos_historial, outputs=archivo_historial)

if __name__ == "__main__":
    demo.launch(theme=ai_startup_theme, css=css, js=js_code)
