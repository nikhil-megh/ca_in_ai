import matplotlib.pyplot as plt

def plot_shares():
    # Data (in percent)
    data = {
        "US": {
            "Consumption": 24.09,
            "Labor": 4.89,
            "Capital": 23.24,
            "AI Patent": 42.05,
            "Non-AI Patent": 30.89
        },
        "China": {
            "Consumption": 8.70,
            "Labor": 25.58,
            "Capital": 6.95,
            "AI Patent": 1.5,
            "Non-AI Patent": 2.83
        },
        "EU": {
            "Consumption": 21.09,
            "Labor": 6.59,
            "Capital": 24.14,
            "AI Patent": 23,
            "Non-AI Patent": 29.31
        }
    }

    # Colors for lines
    region_colors = {"US": "tab:blue", "China": "tab:red", "EU": "tab:green"}

    # Markers for categories
    share_markers = {
        "Consumption": "o",
        "Labor": "s",
        "Capital": "D",
        "AI Patent": "^",
        "Non-AI Patent": "v"
    }

    fig, ax = plt.subplots(figsize=(11, 5))

    # Adjusted y-positions
    y_positions = {
        "EU": 2.8,
        "China": 2.0,
        "US": 1.2
    }

    # Vertical offset for alternating labels
    offset_up = 0.15
    offset_down = -0.15

    for region, y in y_positions.items():
        # Baseline
        ax.hlines(y, xmin=-1, xmax=44, colors=region_colors[region], alpha=0.35, linewidth=4)

        # Sort shares by x-position so alternation is based on left→right order
        sorted_items = sorted(data[region].items(), key=lambda kv: kv[1])

        toggle = 1  # alternate above / below

        for share_name, value in sorted_items:
            # Choose color: black ONLY for consumption
            marker_color = "black" if share_name == "Consumption" else region_colors[region]
            text_color = "black" if share_name == "Consumption" else region_colors[region]

            # Marker
            ax.plot(
                value,
                y,
                marker=share_markers[share_name],
                color=marker_color,
                markersize=10
            )

            # Label offset
            label_offset = offset_up if toggle == 1 else offset_down
            toggle *= -1

            # Label
            ax.text(
                value,
                y + label_offset,
                share_name,
                ha="center",
                va="center",
                fontsize=7,
                color=text_color
            )

    # Axes
    ax.set_yticks([1.2, 2.0, 2.8])
    ax.set_yticklabels(["US", "China", "EU"], fontsize=12)

    ax.set_xlim(-1, 44)
    ax.set_xlabel("Share (%)", fontsize=12)
    ax.set_ylim(0.6, 3.4)

    ax.set_title(
        "2010 Global Shares",
        fontsize=14
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_shares()
