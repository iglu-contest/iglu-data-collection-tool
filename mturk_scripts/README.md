# Data collection for Iglu using Mturk

This directory contains the scripts used to automatically generate and validate Mturk hits for data collection.

Some definitions:
* Starting task: A grid configuration that new games can take as starting points. A starting task can have multiple following turns. When the game branches, the history of previous common turns is shared.
* Game: A game contains multiple turns. A game can be on one of these states:
  * Open: The end goal of the game has not been reached and we need to collect more turns.
  * Closed: A human has indicated the end goal of the game has been reached, or the game has failed.
    For multiturn data, this means the target structure was achieved.
    For singleturn data, this means the maximum number of turns have been reached.
* Turn: consecutive activity of a single player with starting grid, end grid, and tape of player actions The starting grid of the first turn and end grid of the last turn are considered the starting and ending grid of the entire game. A turn can be on one of these states:
  * Open: There is a created hit on the turn that needs to be completed and validated. While the HIT is active, a new assignments can be received, processed and approved for the turn, changing its state to Closed. If the HIT is already expired, no new assignments can be received, and the turn will remain Open.
  * Closed or validated: The turn has been validated and there are no incomplete HITs associated.


## Singleturn collection

Single turn collection is a strategy to generate instructions and target structures that does not depend on sequential turn taking by different annotators acting as architects and builder. Instead, a single annotator plays both roles, by giving instructions and building the expected structure at the same time.

The general structure of the HITs are:

* An interactive agent, controlled by the annotator, is dropped in the middle of an ongoing game where the structure is built partially. The partially completed game is retrieved from the multi-turn interactions
dataset mentioned above.
* Annotators must perform a sequence of actions of their choosing for a duration of one minute.
* After the minute has passed, the annotator describes their performed set of actions in natural language in the form of instructions.

To improve quality, we tag a hit as accepted by some heuristic criteria, including but not limited to the given instruction must be in "English," and the length of the instructions should not very short.