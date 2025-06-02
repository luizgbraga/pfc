import matplotlib.pyplot as plt

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

plt.figure(figsize=(8, 8))
wedges, texts, autotexts = plt.pie(
    values,
    labels=None,
    autopct=lambda pct: f"{int(pct/100.*sum(values))}",
    startangle=90,
    colors=plt.cm.Paired.colors,
    wedgeprops={"edgecolor": "black"},
)

plt.legend(
    wedges,
    labels,
    title="Conceitos",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),
    fontsize=10,
    borderaxespad=0.5,
    borderpad=1.1,
)

plt.tight_layout()

plt.savefig("concepts.png", dpi=300, bbox_inches="tight")

plt.show()
