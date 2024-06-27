from pathlib import Path
from config import Config
import pandas as pd
import numpy as np
import os

BEAM_DIR = "beam/repos/routing_monitor/detection_result/wide"
METRIC_COL = "diff_balance"


# ! Copy pasted from repos/anomaly_detector/report_anomaly_routeviews.py
# We are unable to import this function as they run code in the main block !
# This was copied on 24/06/2024
def metric_threshold(df, metric_col):
    values = df[metric_col]
    mu = np.mean(values)
    sigma = np.std(values)
    metric_th = mu+4*sigma

    # print("reference metric: ")
    # print(values.describe())
    # print(f"metric threshold: {metric_th}")

    return metric_th


class ThresholdPollution():
    """
        This class is an experiment on how to pollute the BEAM threshold.
        As the threshold is calculated based on the mean and std of the metric,
        we can pollute the data by adding some outliers to the data.
        We inject only paths that do not go above the threshold, to not raise alarms.
    """

    def __init__(self):
        print("Loading BEAM pollution data")
        if not os.path.exists(Config.BEAM_POLLUTION_DIR):
            raise Exception(f"BEAM pollution data directory \
                             not found: {Config.BEAM_POLLUTION_DIR}. Did you unzip the archive?")

        if not os.path.exists(BEAM_DIR):
            raise Exception(f"BEAM routing data directory \
                             not found: {BEAM_DIR}. Did you run the script?")

        self.polluted_df = self.load_metric_file(
            f"{Config.BEAM_POLLUTION_DIR}/BEAM_metric/first_20240301.0100.bm.csv",
            f"{Config.BEAM_POLLUTION_DIR}/route_change/first_20240301.0100.csv")

    def pollute(self):
        print("Polluting BEAM data")
        folder_metric_p = Path(BEAM_DIR+"/BEAM_metric")
        files_in_metric = sorted(folder_metric_p.glob("*.csv"))

        previous_m_file = files_in_metric[0]
        previous_rc_file = Path(
            f"{BEAM_DIR}/route_change/{previous_m_file.stem.replace('.bm', '')}.csv")
        df_p = self.load_metric_file(previous_m_file, previous_rc_file)

        # iterate skipping the first file
        for i in range(1, len(files_in_metric)):
            print("Polluting Hour: ", files_in_metric[i].stem)
            # Previous
            th = metric_threshold(df_p, METRIC_COL)
            mean = np.mean(df_p[METRIC_COL])
            print(f"Hour-1: Threshold: {th}, Mean: {mean}")

            # find the most far values from the mean in self.polluted so that we can worsen the std
            # and make the threshold higher
            self.polluted_df["distance_from_mean"] = abs(
                self.polluted_df[METRIC_COL] - mean)
            df_ordered_polluted = self.polluted_df.sort_values(
                by="distance_from_mean", ascending=False)
            df_ordered_polluted = df_ordered_polluted[df_ordered_polluted[METRIC_COL] < th-(
                th*0.1)]

            # Current
            current_m_file = files_in_metric[i]
            current_rc_file = Path(
                f"{BEAM_DIR}/route_change/{current_m_file.stem.replace('.bm', '')}.csv")
            df_c = self.load_metric_file(current_m_file, current_rc_file)
            th = metric_threshold(df_c, METRIC_COL)
            mean = np.mean(df_c[METRIC_COL])
            print(f"Hour: Threshold: {th}, Mean: {mean}")

            # add 50 of the df_ordered_polluted to the current df
            df_c = pd.concat([df_c, df_ordered_polluted[:50]])
            th = metric_threshold(df_c, METRIC_COL)
            mean = np.mean(df_c[METRIC_COL])
            print(f"Polluted: Threshold: {th}, Mean: {mean}")

            df_p = df_c

    def load_metric_file(self, metric_path, route_change_path):
        metric_df = pd.read_csv(metric_path, sep=",")
        route_change_df = pd.read_csv(route_change_path, sep=",")
        df = pd.concat([metric_df, route_change_df], axis=1)

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna(how="any")

        dedup_index = ["prefix1", "prefix2", "forwarder", "path1", "path2"]
        df = df.drop_duplicates(dedup_index, keep="first",
                                inplace=False, ignore_index=True)

        df = self.calculate_metric(df)
        return df

    def calculate_metric(self, df):
        df[METRIC_COL] = df["diff"]/(df["path_d1"]+df["path_d2"])
        return df
