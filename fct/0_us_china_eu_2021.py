import matplotlib.pyplot as plt

def plot_shares():
    # Data (in percent)
    data = {
        "US": {
            "Consumption": 25.37,
            "Labor": 5.02,
            "Capital": 24.37,
            "AI Patent": 35.61,
            "Non-AI Patent": 26.08
        },
        "China": {
            "Consumption": 17.9,
            "Labor": 23.12,
            "Capital": 17.82,
            "AI Patent": 14.79,
            "Non-AI Patent": 11.63
        },
        "EU": {
            "Consumption": 16.45,
            "Labor": 6.31,
            "Capital": 18.29,
            "AI Patent": 14.37,
            "Non-AI Patent": 22.49
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
        ax.hlines(y, xmin=4, xmax=37, colors=region_colors[region], alpha=0.35, linewidth=4)

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

    ax.set_xlim(4, 37)
    ax.set_xlabel("Share (%)", fontsize=12)
    ax.set_ylim(0.6, 3.4)

    ax.set_title(
        "2021 Global Shares",
        fontsize=14
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_shares()
