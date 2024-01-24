import argparse
import torch
import numpy as np

from pathlib import Path
from typing import List, Mapping, Sequence
from abc import ABC, abstractmethod

import taichi as ti
import torch

from synthetic_trees.util.file import load_data_npz
from synthetic_trees.view import paths_from_args, view_synthetic_data
from synthetic_trees.data_types.cloud import Cloud

from taichi_perlin import dropout_3d

params = {
    "noise_scale": [0.5, 1.0],
    "octaves": 6,
    "freq_multiplier": 1.2,
    "dropout": [0.0, 0.2],
    "peturb": [0.1, 0.4],
    "peturb_bias": 0.5,
    "peturb_distance": [0.0, 0.006],
}


class Augmentation(ABC):
    @abstractmethod
    def __call__(self, cloud: Cloud) -> Cloud:
        pass


class Dropout3D(Augmentation):
    def __init__(self, **kwargs):
        kwargs = {
            k: tuple(v) if isinstance(v, Sequence) else v for k, v in kwargs.items()
        }

        self.params = dropout_3d.DropoutParams(**kwargs)
        self.dropout = dropout_3d.PointDropout(self.params)

    def __call__(self, cloud, seed=None):
        points, mask = self.dropout(cloud.xyz, seed)
        cloud.xyz = cloud.xyz[mask]
        cloud.rgb = cloud.rgb[mask]
        cloud.medial_vector = cloud.medial_vector[mask]

        return cloud


def parse_args():
    parser = argparse.ArgumentParser(description="Visualizer Arguments")

    parser.add_argument(
        "file_path",
        help="File Path of tree.npz",
        default=None,
        type=Path,
    )

    parser.add_argument(
        "-lw",
        "--line_width",
        help="Width of visualizer lines",
        default=1,
        type=int,
    )
    return parser.parse_args()


def main():
    ti.init()
    args = parse_args()
    data = [(load_data_npz(filename), filename) for filename in paths_from_args(args)]

    # print(data)

    aug = Dropout3D(**params)

    for (cld, skeleton), path in data:
        cld.to_device(torch.device("cuda"))

        cld = aug(cld)
        cld.to_device(torch.device("cpu"))

    view_synthetic_data(data, args.line_width)


if __name__ == "__main__":
    main()
