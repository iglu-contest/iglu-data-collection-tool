# Single turn data collection for Iglu using Mturk

This directory contains the scripts used to automatically generate and validate Mturk hits for single-turn data collection.

Definitions:
* World state: a description of the game at any point. It includes both block configuration, i.e. the grid with the placement and types of blocks, and player position. However, the player position is only relevant during the turn while the player is taking actions. The starting and ending states of a turn include only the block configuration
* Game: A game contains multiple turns. A game can be on one of these states:
  * Open: The end goal of the game has not been reached and we need to collect more turns.
  * Closed: A human has indicated the end goal of the game has been reached.
    For multiturn data, this means the target structure was achieved.
    For singleturn data, this means the maximum number of turns have been reached.
  * Running: there is a created hit on the game that needs to be completed and validated
  * Failed:
* Turn: consecutive activity of a single player with starting structure, end structure, and tape of player actions.
  * The starting structure of the first turn and end structure of the last turn are considered the starting and ending strutures of the entire game.
* Tape: TODO

## How does single turn collection works

Single turn collection is a strategy to generate instructions and target structures that does not depend on sequential turn taking by different annotatores acting as architects and builder. Intead, a single annotator plays both roles, by giginv instructions and building the expected structure at the same time.

### Data storage

Game data is composed of four types of data: game metadata (game id, turn id, etc.), utterances, world description and sequence of player's actions. Game metadata and utterances are stored in Azure tables,
while the world and player's actions are stored in json files in Azure containers.

The initial structures are random turns of previous games, and share the same format as the end structures. The end structure of a turn is read from the turn json file and taken as initial structure of the next turn.

TODO Azure table description

TODO Azure Storage containers description

## HIT structure and Voxelworld

The html layout of the HIT will record the annotator's actions in the volxelworld. It will automatically store the world state and actions into Azure Storage on submission. The responses to the hit questions will be retrieved normally from the HIT through the boto3 API.
