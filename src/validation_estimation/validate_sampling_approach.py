'''
    This script test the random sampling approach. It evaluates how big the
    samples size has to be to give reproducable and therefore comparable
    results.
'''
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, "..")
from utils import RESULTSPATH, SEGMENTS, DATASET_STRAIN_DICT
from utils import get_sequence, load_all, create_sampling_space, calculate_direct_repeat, get_dataset_names


def plot_distribution(pos_dict: dict, name: str)-> None:
    '''
        Gets the sampled starting positions for each segment and shows the
        distribution of them on the sequence.
        :param pos_dict: segment as key and list with positions as value
        :param name: prefix for the filename including straing (and author)

        :return: None
    '''
    fig, axs = plt.subplots(4, 2, figsize=(5, 7), tight_layout=True)
    i = 0
    j = 0
    for k, v in pos_dict.items():
        if len(v) == 0 or min(v) == max(v):
            continue
        axs[i,j].hist(v, bins=max(v)-min(v))
        axs[i,j].set_xlabel("position on sequence")
        axs[i,j].set_ylabel("count")
        axs[i,j].set_xlim(left=min(v), right=max(v))
        axs[i,j].set_title(f"{name}")
        
        i = i + 1
        if i == 4:
            j = 1
            i = 0

    fig.suptitle("Distribution of randomly sampled start positions")
    fname = f"{name}_distribution_sampling.png"
    savepath = os.path.join(RESULTSPATH, "validation_estimation", fname)
    plt.savefig(savepath)
    plt.close()


def test_sampling_approach(dfs: list, dfnames: list)-> None:
    '''
        Tests the sampling approach by generating increasingly bigger sets and
        comparing the mean of the start positions. When the difference of the
        mean of the last two batches are smaller than 0.1 % the testing is
        stopped.

        :return: None
    '''
    plt.rc("font", size=12)
    for df, dfname in zip(dfs, dfnames):
        print(dfname)
        fig, axs = plt.subplots(1, 1, figsize=(5, 5), tight_layout=True)
        starts_dict = dict()
        ends_dict = dict()
        for seg in SEGMENTS:
            v_s = df.loc[(df["Segment"] == seg)]
            if len(v_s.index) <= 1:
                starts_dict[s] = list()
                ends_dict[s] = list()
                continue

            seq = get_sequence(DATASET_STRAIN_DICT[dfname], seg)
            start = int(v_s["Start"].mean())
            end = int(v_s["End"].mean())
            s = (max(start-200, 50), start+200)
            e = (end-200, min(end+200, len(seq)-50))

            means = list()
            batch_size = 100
            thresh = -1
            thresh_m = 0
            sampl_data = create_sampling_space(seq, s, e)

            rounds = np.arange(batch_size, 70*batch_size+1, batch_size)
            counters = list()
            for n in rounds:
                sampling_data = sampl_data.sample(n)

                for _, r in sampling_data.iterrows():
                    counter, _ = calculate_direct_repeat(seq, r["Start"], r["End"], 5)
                    counters.append(counter)

                means.append(np.mean(counters))

                if len(means) > 1:
                    # difference is 0.1 % np.mean(means)
                    if abs(means[-1] - means[-2]) < np.mean(means) * 0.001 and thresh == -1:
                        thresh = n
                        thresh_m = means[-1]

            starts_dict[s] = sampling_data["Start"].to_list()
            ends_dict[s] = sampling_data["End"].to_list()

            axs.scatter(rounds, means, label=seg)
            axs.scatter(thresh, thresh_m, c="black", marker="x")

        axs.set_xlabel("number of samples")
        axs.set_ylabel("mean of direct repeat lengths")
        axs.set_title(f"{dfname}")
        axs.legend()
        
        save_path = os.path.join(RESULTSPATH, "validation_estimation")
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        fname = f"{dfname}_testing_sampling.png"
        plt.savefig(os.path.join(save_path, fname))
        plt.close()

        plot_distribution(starts_dict, f"{dfname}_start")
        plot_distribution(ends_dict, f"{dfname}_end")


if __name__ == "__main__":
    plt.style.use("seaborn")
    RESULTSPATH = os.path.dirname(RESULTSPATH)

    dfnames = get_dataset_names(cutoff=50)
    dfs, _ = load_all(dfnames)

    test_sampling_approach(dfs, dfnames)

