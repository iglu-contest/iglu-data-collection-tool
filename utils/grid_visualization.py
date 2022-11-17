# from https://gitlab.aicrowd.com/aicrowd/challenges/iglu-challenge-2022/iglu-2022-rl-mhb-baseline/-/blob/master/agents/mhb_baseline/nlp_model/utils.py

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator


def plot_grid(voxel, text=None, figsize=(6,6), fontsize=10):
    idx2color = {1: 'blue', 2: 'green', 3: 'red', 4: 'orange', 5: 'purple', 6: 'yellow'}
    vox = voxel.transpose(1, 2, 0)
    colors = np.empty(vox.shape, dtype=object)
    for i in range(vox.shape[0]):
        for j in range(vox.shape[1]):
            for k in range(vox.shape[2]):
                if vox[i, j, k] != 0:
                    colors[i][j][k] = str(idx2color[vox[i, j, k]])

    fig = plt.figure(figsize=figsize, dpi=200)
    ax = fig.add_subplot(projection='3d', )
    ax.voxels(vox, facecolors=colors, edgecolor='k', )

    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=11))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=11))
    ax.zaxis.set_major_locator(MaxNLocator(integer=True, nbins=9))
    ax.set_xticks(np.arange(0, 12, 1), minor=True)
    ax.set_yticks(np.arange(0, 12, 1), minor=True)
    ax.set_zticks(np.arange(0, 9, 1), minor=True)

    box = ax.get_position()
    box.x0 = box.x0 - 0.05
    box.x1 = box.x1 - 0.05
    box.y1 = box.y1 + 0.16
    box.y0 = box.y0 + 0.16
    ax.set_position(box)

    if text is not None:
        plt.annotate(text, (0, 0), (0, -20), xycoords='axes fraction', textcoords='offset points',
                     verticalalignment='top', wrap=True, fontsize=fontsize)
    return fig
    
    
def break_str_to_lines(text, max_char_len=50):
    lines = []
    current_line = ''
    for i, ch in enumerate(text):
        if len(current_line) > max_char_len and ch == ' ':
            lines.append(current_line)
            current_line = ''
        current_line += ch
    lines.append(current_line)
    return '\n'.join(lines)