import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import re
from matplotlib.patches import Patch

# ---------------- Dados ----------------
time_data = {
    "Modelo": ["qwen-2.5-7b","qwen-2.5-7b","qwen-2.5-7b",
               "qwen-3-14b","qwen-3-14b","qwen-3-14b",
               "deepseek","deepseek","deepseek",
               "qwen3-80b","qwen3-80b","qwen3-80b",
               "llama-3.3-70b","llama-3.3-70b","llama-3.3-70b"],
    "Log": ["Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3"],
    "Baseline": [9.71, 10.73, 10.23, 116.03, 61.81, 61.33, 79.69, 43.52, 43.57, 50, 15, 36, 46, 52, 49],
    "GraphRAG": [13.82, 14.81, 12.76, 139.76, 106.76, 96.61, 59.39, 87.05, 115.68, 55, 17, 37, 50, 57, 52]
}

subgraph_data = {
    "Modelo": ["qwen-2.5-7b","qwen-2.5-7b","qwen-2.5-7b",
               "qwen-3-14b","qwen-3-14b","qwen-3-14b",
               "deepseek","deepseek","deepseek",
               "qwen3-80b","qwen3-80b","qwen3-80b",
               "llama-3.3-70b","llama-3.3-70b","llama-3.3-70b"],
    "Log": ["Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3",
            "Log 1","Log 2","Log 3"],
    "Nos": [2,1,1,48,5,5,1,5,5,49,11,36,46,52,49],
    "Relacionamentos": [0,0,0,43,0,0,0,0,0,50,7,37,47,55,57]
}

df_time = pd.DataFrame(time_data)
df_subgraph = pd.DataFrame(subgraph_data)
df = pd.merge(df_time, df_subgraph, on=["Modelo","Log"])

# ---------------- Extrair tamanho do modelo ----------------
def extrair_tamanho(modelo):
    match = re.search(r'(\d+(\.\d+)?)b', modelo)
    return float(match.group(1)) if match else 20.0

df["Tamanho"] = df["Modelo"].apply(extrair_tamanho)
df["Familia"] = df["Modelo"].apply(lambda x: "qwen" if "qwen" in x else ("llama" if "llama" in x else "deepseek"))
df["Subgrafo"] = df["Nos"] + df["Relacionamentos"]

# ---------------- Gráfico unificado ----------------
plt.figure(figsize=(10,7))
colors = {"qwen":"blue","llama":"green","deepseek":"red"}

for familia in df["Familia"].unique():
    df_fam = df[df["Familia"]==familia]
    plt.scatter(df_fam["Tamanho"], df_fam["GraphRAG"], 
                s=df_fam["Subgrafo"]*20,  # escala marcador pelo subgrafo
                c=colors[familia],
                alpha=0.6,
                edgecolors='w',  # contorno para visibilidade
                linewidth=0.5,
                label=familia)

# Ajustar limites do eixo y para não cortar círculos
y_max = df["GraphRAG"].max()
s_max = df["Subgrafo"].max() * 20
plt.ylim(0, y_max + np.sqrt(s_max))  # adiciona espaço extra proporcional ao maior marcador

# Legenda apenas com cores
legend_elements = [Patch(facecolor=colors[f], label=f) for f in df["Familia"].unique()]
plt.legend(handles=legend_elements, title="Família")

plt.xlabel("Tamanho do Modelo (B)")
plt.ylabel("Tempo GraphRAG (s)")
plt.title("Tempo de execução x Tamanho do Modelo x Tamanho do Subgrafo por Família")
plt.grid(True)
plt.show()
