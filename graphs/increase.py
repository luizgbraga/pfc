import matplotlib.pyplot as plt
import pandas as pd
import re

# ---------------- Dados completos ----------------
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

df = pd.DataFrame(time_data)

# ---------------- Calcular aumento percentual ----------------
df['Aumento_pct'] = (df['GraphRAG'] - df['Baseline']) / df['Baseline'] * 100

# Média por modelo
df_pct = df.groupby('Modelo')['Aumento_pct'].mean().reset_index()

# ---------------- Plotar gráfico de barras ----------------
plt.figure(figsize=(10,6))
bars = plt.bar(df_pct['Modelo'], df_pct['Aumento_pct'], color='skyblue')

plt.ylabel('Aumento de Tempo (%)')
plt.xlabel('Modelo')
plt.title('Aumento percentual médio de tempo de execução com GraphRAG')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Adicionar valores de percentual acima das barras
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 1, f'{height:.1f}%', ha='center', va='bottom')

plt.tight_layout()
plt.show()
