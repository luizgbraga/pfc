import matplotlib.pyplot as plt

# Data (removed last category as per your request)
labels = [
    "ObservableObject",
    "Facet",
    "UcoObject",
    "WindowsPEOptionalHeader",
    "EmailMessageFacet",
    "ContactFacet",
    "Hash",
    "WindowsTaskFacet",
    "ComputerSpecificationFacet",
]
values = [279, 119, 62, 32, 30, 26, 24, 22, 22]

# Plot
plt.figure(figsize=(8, 8))
wedges, texts, autotexts = plt.pie(
    values,
    labels=None,  # We won't display the labels on the pie chart itself
    autopct=lambda pct: f"{int(pct/100.*sum(values))}",
    startangle=90,
    colors=plt.cm.Paired.colors,
    wedgeprops={"edgecolor": "black"},
)

# Add the legend with the labels
plt.legend(
    wedges,
    labels,
    title="Conceitos",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),
    fontsize=10,
    borderaxespad=0.5,  # distância entre a legenda e o gráfico
    borderpad=1.1,  # padding interno da caixa da legenda
)

# Equal aspect ratio ensures that pie is drawn as a circle.
plt.title(
    "Conceitos da UCO com mais de 20 relacionamentos", fontsize=14, fontweight="bold"
)
plt.tight_layout()

# Save the plot as a PNG file
plt.savefig("concepts.png", dpi=300, bbox_inches="tight")

# Show the plot
plt.show()
