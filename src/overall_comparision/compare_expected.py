'''
    Performs analyses of direct repeats and nucleotide enrichment of the
    datasets while comparing the results to data that would be expected by
    chance.
'''
import os
import sys

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

sys.path.insert(0, "..")
from utils import load_all
from utils import get_sequence, count_direct_repeats_overall, get_p_value_symbol, create_nucleotide_ratio_matrix, plot_heatmap, get_dataset_names
from utils import SEGMENTS, RESULTSPATH, NUCLEOTIDES
from overall_comparision.general_analyses import deletion_site_motifs


def plot_expected_vs_observed_nucleotide_enrichment_heatmaps(dfs: list, dfnames: list, expected_dfs: list, compared: str, folder: str="compare_expected")-> None:
    '''
        plot difference of expected vs observed nucleotide enrichment around
        deletion junctions as heatmap.
        :param dfs: The list of DataFrames containing the data, preprocessed
            with sequence_df(df)
        :param dfnames: The names associated with each DataFrame in `dfs`
        :param expected_dfs: The list of DataFrames containing the expected
            data, preprocessed with sequence_df(df)
        :param compared: defines in title what data is compared
        :param folder: defines where to save the results
    
        :return: None

    '''
    fig, axs = plt.subplots(figsize=(10, len(dfs)/2), nrows=2, ncols=2)
    axs = axs.flatten()

    for i, nuc in enumerate(NUCLEOTIDES.keys()):
        x = list()
        y = list()
        vals = list()
        val_labels = list()
        for dfname, df, expected_df in zip(dfnames, dfs, expected_dfs):
            df = df.reset_index()
            probability_matrix = create_nucleotide_ratio_matrix(df, "seq_around_deletion_junction")
            n_samples = len(df)
            expected_probability_matrix = create_nucleotide_ratio_matrix(expected_df, "seq_around_deletion_junction")
            n_samples2 = len(expected_df)
            for j in probability_matrix.index:
                x.append(j)
                y.append(dfname)

                p1 = probability_matrix.loc[j,nuc]
                p2 = expected_probability_matrix.loc[j,nuc]
                if n_samples < n_samples2:
                    n_s = n_samples
                else:
                    n_s = n_samples2
                n_s = min(n_s, 1000)
                n_samples2 = min(n_samples2, 1000)
                test_array = np.concatenate((np.ones(int(n_s * p1)), np.zeros(int(n_s - n_s * p1))))
                test_array2 = np.concatenate((np.ones(int(n_samples2 * p2)), np.zeros(int(n_samples2 - n_samples2 * p2))))
                # perform an ANOVA as done in Alaji2021
                pval =  stats.f_oneway(test_array, test_array2).pvalue

                diff = p1 - p2
                vals.append(diff)
                if pval < 0.00001:
                    pval_symbol = "**"
                elif pval < 0.0001:
                    pval_symbol = "*"
                else:
                    pval_symbol = ""
                val_labels.append(pval_symbol)
        if len(vals) != 0:        
            m = abs(min(vals)) if abs(min(vals)) > max(vals) else max(vals)
        else:
            m = 0
        axs[i] = plot_heatmap(x,y,vals, axs[i], format=".1e", cbar=True, vmin=-m, vmax=m, cbar_kws={"pad": 0.01})
        for v_idx, val_label in enumerate(axs[i].texts):
            val_label.set_text(val_labels[v_idx])
            val_label.set_size(10)
        axs[i].set_title(f"{NUCLEOTIDES[nuc]}")
        axs[i].set_ylabel("")
        axs[i].set_yticks([ytick + 0.5 for ytick in range(len(dfnames))])
        axs[i].set_xlabel("")  
        axs[i].set_xticks([xtick - 0.5 for xtick in probability_matrix.index])
        
        quarter = len(probability_matrix.index) // 4
        indexes = [pos for pos in range(1, quarter * 2 + 1)]
        if i % 2 == 0:
            axs[i].set_yticklabels([f"{dfname} ({len(df)})" for dfname,df in zip(dfnames,dfs)])
        else:
            axs[i].set_yticklabels([])
        if i < 2:
            axs[i].xaxis.set_ticks_position("top")
            axs[i].xaxis.set_label_position("top")
        axs[i].set_xticklabels(indexes + indexes, rotation=0)
        xlabels = axs[i].get_xticklabels()
        for x_idx, xlabel in enumerate(xlabels):
            if x_idx < quarter or x_idx >= quarter * 3:
                xlabel.set_color("black")
                xlabel.set_fontweight("bold")
            else:
                xlabel.set_color("grey")   

  #  fig.suptitle(f"Difference of the nucleotide occurrence ({compared})")
    fig.suptitle("Enriched (red) and depleted (blue) nucleotides")
    fig.subplots_adjust(top=0.9)
    fig.tight_layout()
    save_path = os.path.join(RESULTSPATH, folder)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    plt.savefig(os.path.join(save_path, "nuc_occ_diff.png"))
    plt.close()


def plot_expected_vs_observed_direct_repeat_heatmaps(dfs: list, dfnames: list, expected_dfs: list, compared: str, folder: str="compare_expected")-> None:
    '''
        plot difference of expected vs observed direct repeat ratios around
        deletion junctions as heatmap.
        :param dfs: The list of DataFrames containing the data, preprocessed
            with sequence_df(df)
        :param dfnames: The names associated with each DataFrame in `dfs`
        :param expected_dfs: The list of DataFrames containing the expected
            data, preprocessed with sequence_df(df)
        :param compared: defines in title what data is compared
        :param folder: defines where to save the results
    
        :return: None
    '''
    fig, axs = plt.subplots(figsize=(10, 7))
    x = list()
    y = list()
    vals = list()
    # calculate direct repeats
    for dfname, df, expected_df in zip(dfnames, dfs, expected_dfs):
        final_d = dict()
        expected_final_d = dict()
        for s in SEGMENTS:
            df_s = df[df["Segment"] == s]
            expected_df_s = expected_df[expected_df["Segment"] == s]
            n_samples = len(df_s)
            if n_samples == 0:
                continue
            seq = get_sequence(df_s["Strain"].unique()[0], s)            
            counts, _ = count_direct_repeats_overall(df_s, seq)
            for k, v in counts.items():
                if k in final_d:
                    final_d[k] += v
                else:
                    final_d[k] = v

            expected_counts, _ = count_direct_repeats_overall(expected_df_s, seq)
            for k, v in expected_counts.items():
                if k in expected_final_d:
                    expected_final_d[k] += v
                else:
                    expected_final_d[k] = v

        final = np.array(list(final_d.values()))
        expected_final = np.array(list(expected_final_d.values()))
        f_obs = final/final.sum() * 100 # normalize to percentage
        f_exp = expected_final/expected_final.sum() * 100 # normalize to percentage
        _, pvalue = stats.chisquare(f_obs, f_exp) # as in Boussier et al. 2020
        symbol = get_p_value_symbol(pvalue)
        x.extend(final_d.keys())
        y.extend([f"{dfname} ({len(df)}) {symbol}" for _ in range(6)])
        vals.extend(f_obs - f_exp)

    m = abs(min(vals)) if abs(min(vals)) > max(vals) else max(vals)
    axs = plot_heatmap(x,y,vals, axs, vmin=-m, vmax=m, cbar=True, format=".1f")
    axs.set_title(f"Difference in direct repeat distribution ({compared})")
    axs.set_ylabel("")
    axs.set_xlabel("Direct repeat length")
    for v_idx, val_label in enumerate(axs.texts):
        val_label.set_text(f"{val_label.get_text()}")
    x_ticks = axs.get_xticklabels()
    label = x_ticks[-2].get_text()
    x_ticks[-1].set_text(f"> {label}")
    axs.set_xticklabels(x_ticks)
    fig.tight_layout()
    save_path = os.path.join(RESULTSPATH, folder)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    plt.savefig(os.path.join(save_path, "dir_rep_diff.png"))
    plt.close()


if __name__ == "__main__":
    plt.style.use("seaborn")

    dfnames = get_dataset_names(cutoff=50)
    dfs, expected_dfs = load_all(dfnames, expected=True)

    plot_expected_vs_observed_nucleotide_enrichment_heatmaps(dfs, dfnames, expected_dfs, "observed-expected")
    plot_expected_vs_observed_direct_repeat_heatmaps(dfs, dfnames, expected_dfs, "observed-expected")
    deletion_site_motifs(expected_dfs, dfnames, m_len=2, folder="compare_expected")