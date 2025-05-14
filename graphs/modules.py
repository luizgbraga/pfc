import matplotlib.pyplot as plt

# Data
labels = [
    "observable",
    "identity",
    "core",
    "tool",
    "action",
    "marking",
    "types",
    "location",
    "role",
    "pattern",
    "victim",
]
values = [289, 20, 18, 13, 8, 7, 5, 4, 4, 3, 2]
total = sum(values)

# Sort data
sorted_data = sorted(zip(values, labels), reverse=True)
sorted_values, sorted_labels = zip(*sorted_data)

# Plot
plt.figure(figsize=(10, 6))
bars = plt.barh(sorted_labels, sorted_values, color="#4A90E2", edgecolor="black")

plt.xlabel("Quantidade", fontsize=12)
plt.ylabel("Categoria", fontsize=12)
plt.title("Módulos da UCO", fontsize=14, fontweight="bold")
plt.grid(axis="x", linestyle="--", alpha=0.7)
plt.gca().invert_yaxis()  # Highest on top

# Adjust the xlim to avoid overflow (leave some space on the right)
plt.xlim(0, max(sorted_values) * 1.15)  # Add 10% more space on the right

# Add count + percentage labels
for bar, value in zip(bars, sorted_values):
    percentage = value / total * 100
    label = f"{value} ({percentage:.1f}%)"
    plt.text(
        bar.get_width() + 1,
        bar.get_y() + bar.get_height() / 2,
        label,
        va="center",
        fontsize=10,
    )

plt.tight_layout()
plt.savefig("modules.png", dpi=300, bbox_inches="tight")
plt.show()
