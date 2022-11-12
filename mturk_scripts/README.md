# Data collection for Iglu using Mturk

This directory contains the scripts used to automatically generate and validate Mturk hits for data collection.


Definitions:
* Starting task: A grid configuration that games can take as starting points. A starting task can have multiple following turns. When the game branches, the history of previous common turns is shared.
* Game: A game contains multiple turns. A game can be on one of these states:
  * Open: The end goal of the game has not been reached and we need to collect more turns.
  * Closed: A human has indicated the end goal of the game has been reached, or the game has failed.
    For multiturn data, this means the target structure was achieved.
    For singleturn data, this means the maximum number of turns have been reached.
  * Running: there is a created hit on the game that needs to be completed and validated
* Turn: consecutive activity of a single player with starting grid, end grid, and tape of player actions.
  * The starting grid of the first turn and end grid of the last turn are considered the starting and ending grid of the entire game.


## Singleturn collection

Single turn collection is a strategy to generate instructions and target structures that does not depend on sequential turn taking by different annotators acting as architects and builder. Instead, a single annotator plays both roles, by giving instructions and building the expected structure at the same time.
