from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
from dfoh import utils
import pandas as pd
import seaborn as sns
import os


class HijackPlot:
    def __init__(self, min_runs=5):
        self.folder = "dfoh/data"
        self.min_runs = min_runs
        self.topology = utils.load_topo()
        self.load_data()

    def plot(self):
        for country in self.data:
            # calculate the percentage of hijacked links
            self.data[country] = [
                (x / self.topology.number_of_nodes()) * 100 for x in self.data[country]]

        def _sort(item):
            sum_ = sum(item[1])
            return sum_

        # order by the sum of the hijacked links
        self.data = dict(
            sorted(self.data.items(), key=lambda item: _sort(item)))

        x_labels = []
        for c in self.data:
            as_, country, size = c.split("_")
            x_labels.append(f"{as_} ({country}, {str.lower(size)})")

        df = pd.DataFrame(
            {f"Poisoning iteration {i}": [c[i] for c in self.data.values()]
                for i in range(self.min_runs+1)},
            index=x_labels
        )

        df.rename(
            columns={"Poisoning iteration 0": "Original knowledge base"}, inplace=True)

        sns.set_theme(style="darkgrid")
        custom_palette = ["#61A77F"]
        palette = sns.color_palette("light:r", as_cmap=False)
        palette[0] = custom_palette[0]
        adjusted_palette = LinearSegmentedColormap.from_list(
            "adjusted", palette)

        df.plot(kind='bar', stacked=True, figsize=(19, 5),
                colormap=adjusted_palette, linewidth=0)

        plt.legend()
        # plt.title("Hijacks after 5 iterations per AS")
        plt.xlabel("Hijacker AS")
        plt.ylabel("Portion of undetected routes (%)")

        plt.ylim(0, 65)

        plt.xticks(rotation=70, ha='right', rotation_mode='anchor')

        print("Saving plot in dfoh/data")

        plt.savefig("dfoh/data/hijack.png", dpi=600, bbox_inches='tight')
        plt.savefig("dfoh/data/hijack.pdf", dpi=600, bbox_inches='tight')

    def load_data(self):
        self.data = {}
        for folder in os.listdir(self.folder):
            if not os.path.isdir(f"{self.folder}/{folder}"):
                continue

            runs = os.listdir(f"{self.folder}/{folder}")
            if len(runs) < self.min_runs:
                print(
                    f"Skipping {folder} because it has less than {self.min_runs} runs.")
                continue

            as_ = folder.split("_")[0]
            self.data.setdefault(folder, []).append(self.topology.degree(as_))

            skip = False
            for i in range(self.min_runs):
                file = f"{self.folder}/{folder}/{i}/parsed_results.txt"
                if not os.path.exists(file):
                    print(f"Skipping {folder} because {file} does not exist.")
                    skip = True
                    break

                leg_edges = utils.load_leg(i, f"{self.folder}/{folder}")
                self.data.setdefault(folder, []).append(len(leg_edges))

            if skip:
                self.data[folder]
                continue
