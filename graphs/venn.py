from matplotlib import pyplot as plt
from matplotlib_venn import venn2

# depict venn diagram
venn2(subsets=(292, 258, 39), set_labels=("LLM, Knowledge Graph", "Graph-RAG"))

plt.savefig("venn_diagram.png", dpi=300, bbox_inches="tight")

plt.show()
