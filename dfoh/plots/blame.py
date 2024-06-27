from dfoh import utils
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os


class BlamePlot:
    def __init__(self):
        self.topology = utils.load_topo()

    def plot(self):
        self.load_data("blamed")
        self._plot("blame")
        self.load_data("blamed_hijacked")
        self._plot("blame_hijacked")

    def _plot(self, file_name):
        plt.figure(figsize=(8, 5))
        sns.set_theme(style="darkgrid")

        # palette = ["#E9D0D1", "#DFAFB1", "#D68F91", "#C44E52"]
        palette = ["#F19A9B", "#D54D88", "#7B2A95", "#461765"]
        # palette = ["#9ED5CD", "#44A7CB", "#2E62A1", "#192574"]
        # palette = ["#FBDB68", "#EF9C49", "#E45E2D", "#8B412B"]

        sns.set_palette(palette)

        def custom_sort(k):
            # Define the order for "SMALL", "MEDIUM", "BIG"
            order = {"SMALL": 0, "MEDIUM": 1, "LARGE": 2}
            # Split the key and get the part that indicates size
            size_part = k.split("_")[2] if len(k.split("_")) > 2 else "SMALL"
            # Return a tuple that represents the sort order
            return order[size_part]

        max_level = len(self.data[list(self.data.keys())[0]])
        data_list = []
        self.data = {k: v for k, v in sorted(
            self.data.items(), key=lambda item: (custom_sort(item[0]), int(item[1][0])))}

        for country, values in self.data.items():
            for i in range(max_level-1):
                percentage = (int(values[i]) /
                              self.topology.number_of_nodes()) * 100
                data_list.append(
                    {"Hijacker ASes (smallest to largest)": country,
                     "Portion of ASes can be blamed (%)": percentage,
                        "Path Length": f"{i+2}-hop distance"})

        df = pd.DataFrame(data_list)
        df["Path Length"] = df["Path Length"].astype("category")

        sns.lineplot(data=df, x="Hijacker ASes (smallest to largest)", y="Portion of ASes can be blamed (%)",
                     hue="Path Length", linewidth=2, style="Path Length", markers=False,
                     dashes=[(1, 0), (4, 2), (1, 0), (4, 2)])
        plt.xticks([])
        plt.legend(ncols=2)

        # plt.title("Blame propagation")
        plt.savefig(f"dfoh/data/{file_name}.png", dpi=600, bbox_inches='tight')
        plt.savefig(f"dfoh/data/{file_name}.pdf", dpi=600, bbox_inches='tight')

    def load_data(self, file_name):
        """
        Load the data from the file and plot it.
        """
        self.data = {}
        data_fld = "dfoh/data"

        if not os.path.exists(data_fld):
            raise ValueError(f"Folder {data_fld} does not exist.")

        for country in os.listdir(data_fld):
            if not os.path.isdir(f"{data_fld}/{country}"):
                continue

            if not os.path.exists(f"{data_fld}/{country}/{file_name}.txt"):
                continue

            with open(f"{data_fld}/{country}/{file_name}.txt", "r") as f:
                self.data[country] = [line.strip() for line in f]
