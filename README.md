
# Interactive Grounded Language Understanding in a Collaborative Environment
--

The primary goal of the IGLU project is to approach the problem of how
to develop interactive agents that learn to solve a task while provided with grounded natural language
instructions in a collaborative environment.

Following this objective, the project has collected several datasets with different types of interactions during a block building task. The data and scripts used to collect it will be progressively released in this repository.

Due to the complexity of a general interactive task, the problem is simplified to interactions inside of a finite, Minecraft-like world of blocks. The goal of the interaction is to build a structure using a limited number of block types, which can vary in complexity. Examples of possible target structures to build are:

![Shots of three possible target structures to build](./resources/imgs/voxelworld_combined_shots.png)

 Two roles arise: the Architect is provided with a target structure that needs to be built by the Builder. The Architect provides instructions to the Builder on how to create the target structure and the Builder can ask clarifying questions to the Architect if an instruction is unclear.

The progression of each game is recorded, corresponding to the construction of a target structure
by an Architect and Builder pair, as a discrete sequence of game observations. Each observation
contains the following information: 1) a time stamp, 2) the chat history up until that point in time,
3) the Builder’s position (a tuple of real-valued x, y, z coordinates as well as pitch and yaw angles,
representing the orientation of their camera), 4) the Builder’s block inventory, 5) the locations of
the blocks in the build region.

<img src="./resources/imgs/voxelwrold_building_dialog.gif" width="420" height="280" alt="Gif with interactions between Architect and Builder"/>

## Datasets

This tool was used to collect multi-modal data for the IGLU competiton which is publicly available in this [repo](https://github.com/microsoft/iglu-datasets).

## References

The described datasets are collected as a part of [IGLU:Interactive Grounded Language Understanding in a Collaborative Environment](https://www.aicrowd.com/challenges/neurips-2022-iglu-challenge), which is described in the following papers:

```
@article{mohanty2022collecting,
  title={Collecting Interactive Multi-modal Datasets for Grounded Language Understanding},
  author={Mohanty, Shrestha and Arabzadeh, Negar and Teruel, Milagro and Sun, Yuxuan and Zholus, Artem and Skrynnik, Alexey and Burtsev, Mikhail and Srinet, Kavya and Panov, Aleksandr and Szlam, Arthur and others},
  journal={arXiv preprint arXiv:2211.06552},
  year={2022}
}
```

```
@inproceedings{kiseleva2022interactive,
  title={Interactive grounded language understanding in a collaborative environment: Iglu 2021},
  author={Kiseleva, Julia and Li, Ziming and Aliannejadi, Mohammad and Mohanty, Shrestha and ter Hoeve, Maartje and Burtsev, Mikhail and Skrynnik, Alexey and Zholus, Artem and Panov, Aleksandr and Srinet, Kavya and others},
  booktitle={NeurIPS 2021 Competitions and Demonstrations Track},
  pages={146--161},
  year={2022},
  organization={PMLR}
}
```

```
@article{kiseleva2022iglu,
  title={Iglu 2022: Interactive grounded language understanding in a collaborative environment at neurips 2022},
  author={Kiseleva, Julia and Skrynnik, Alexey and Zholus, Artem and Mohanty, Shrestha and Arabzadeh, Negar and C{\^o}t{\'e}, Marc-Alexandre and Aliannejadi, Mohammad and Teruel, Milagro and Li, Ziming and Burtsev, Mikhail and others},
  journal={arXiv preprint arXiv:2205.13771},
  year={2022}
}
```

Consider citing the papers above if you use the assets for your research.

## License
See here for [MIT License] (https://github.com/iglu-contest/iglu-data-collection-tool?tab=MIT-1-ov-file#readme)

