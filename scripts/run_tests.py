import pandas as pd
from app import optimizar_prompt, procesar_batch, leer_historial
import time
import os

prompts = [
    "escribe un cuento de terror corto",
    "haz una tabla nutricional para una dieta keto",
    "codigo en python para sumar dos numeros",
    "explicame la fisica cuantica como si tuviera 5 años",
    "crea un post para instagram sobre mi nueva cafeteria",
    "dame ideas para un regalo de aniversario",
    "escribe un correo para pedir un aumento de sueldo",
    "resume el concepto de inteligencia artificial",
    "haz un script de bash para hacer backup",
    "dame una rutina de ejercicios en casa"
]

# Crear un CSV temporal para probar el batch (usaremos los últimos 5)
batch_df = pd.DataFrame({"Prompt": prompts[5:]})
batch_df.to_csv("test_batch.csv", index=False)

class DummyFile:
    def __init__(self, name):
        self.name = name

resultados = []

print("Iniciando pruebas individuales (5 prompts)...")
for i in range(5):
    print(f"Probando {i+1}/5: {prompts[i]}")
    opt, var, exp = optimizar_prompt(prompts[i], "", "Profesional", intentos_maximos=3)
    resultados.append({
        "Original": prompts[i],
        "Optimizado": opt,
        "Variables": var,
        "Explicacion": exp,
        "Metodo": "Individual"
    })
    time.sleep(1) # wait 1 sec to avoid rate limits
    
print("Iniciando prueba masiva (Batch) con los otros 5 prompts...")
batch_file = DummyFile("test_batch.csv")
output_path, status = procesar_batch(batch_file)
print(f"Batch completado: {status}")

if output_path and os.path.exists(output_path):
    df_batch = pd.read_csv(output_path)
    for index, row in df_batch.iterrows():
         resultados.append({
            "Original": row.get("Prompt", ""),
            "Optimizado": row.get("Prompt Optimizado", ""),
            "Variables": row.get("Variables Detectadas", ""),
            "Explicacion": row.get("Explicación", ""),
            "Metodo": "Batch"
        })

print("Pruebas completadas. Generando markdown...")

md_content = "# Informe de Pruebas: Optimizador de Prompts (10 Casos)\n\n"
md_content += "Se han evaluado todas las funcionalidades del sistema (Individual y Batch) como usuario.\n\n"

for i, res in enumerate(resultados):
    md_content += f"## Prueba {i+1} ({res['Metodo']})\n"
    md_content += f"**Original:** {res['Original']}\n\n"
    md_content += f"**Variables Detectadas:** `{res['Variables']}`\n\n"
    md_content += f"**Explicación:** {res['Explicacion']}\n\n"
    md_content += f"**Prompt Optimizado:**\n```xml\n{res['Optimizado']}\n```\n\n"
    md_content += "---\n\n"
    
with open("informe.md", "w", encoding="utf-8") as f:
    f.write(md_content)

print("informe.md generado correctamente.")
