import matplotlib.pyplot as plt

years = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015]
counts = [251, 25, 10, 11, 11, 10, 13, 5, 9, 6]

plt.figure(figsize=(10, 6))
bars = plt.bar(years, counts, color='#4A90E2', edgecolor='black')

plt.ylabel('Quantidade', fontsize=12)
plt.xlabel('Ano', fontsize=12)
plt.title('Publicações por ano', fontsize=14, fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.xticks(ticks=years, labels=years)

plt.tight_layout()

plt.savefig('publications_per_year.png', dpi=300, bbox_inches='tight')

plt.show()
