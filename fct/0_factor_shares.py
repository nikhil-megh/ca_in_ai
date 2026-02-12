import matplotlib.pyplot as plt
import numpy as np


def plot_factor_shares():
    # Data
    factors = ["AI Patents", "Non-AI Patents", "Labour", "Capital"]
    countries = ["US", "CN", "EU27", "JP", "KR", "GB", "CA", "CH", "IN", "AU"]

    shares = np.array([
        [31.38, 22.64, 13.12, 12.92, 9.29, 2.61, 1.43, 1.03, 0.85, 0.83],  # AI Patents
        [22.73, 20.79, 19.53, 19.39, 7.00, 2.42, 1.07, 1.90, 0.73, 0.71],  # Non-AI Patents
        [5.04, 21.82, 6.22, 1.96, 0.79, 0.96, 0.56, 0.15, 17.05, 0.41],    # Labour
        [25.39, 18.67, 17.59, 4.54, 1.98, 2.28, 1.55, 0.66, 3.44, 1.69],  # Capital
    ])

    x = np.arange(len(factors))
    width = 0.08  # small width since many bars

    fig, ax = plt.subplots(figsize=(14, 6))

    # Plot each country's bar group
    for i, country in enumerate(countries):
        ax.bar(x + (i - len(countries)/2) * width, shares[:, i], width, label=country)

    ax.set_ylabel("Share (%)")
    ax.set_title("Shares of Factors by Top Countries (2023)")
    ax.set_xticks(x)
    ax.set_xticklabels(factors)
    ax.legend(title="Country", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_factor_shares()
