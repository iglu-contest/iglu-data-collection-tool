# Single turn data collection for Iglu using Mturk

This directory contains the scripts used to automatically generate and validate Mturk hits for single-turn data collection.

### Data storage

Game data is composed of four types of data: game metadata (game id, turn id, etc.), utterances, world description and sequence of player's actions. Game metadata and utterances are stored in Azure tables,
while the world and player's actions are stored in json files in Azure containers.

The initial structures are random turns of previous games, and share the same format as the end structures. The end structure of a turn is read from the turn json file and taken as initial structure of the next turn.

TODO Azure table description

TODO Azure Storage containers description

## HIT structure

The html layout of the HIT will record the annotator's actions in the volxelworld. It will automatically store the world state and actions into Azure Storage on submission. The responses to the hit questions will be retrieved normally from the HIT through the boto3 API.

When creating a HIT, the HIT id is stored in the database, making it possible to add the results of the accepted assignments later.

HITs have a RequesterAnnotation field that we will use to determine which type of hit it is (builder-normal, clarifying-question, etc).


## Testing

* Unittest normal scripts that mock all elements and do not require real credentials.
* Ping scripts that read from resources using real credentials.
* Creation of test hits in sandbox: the script will only create the hit, without updating any
value in the storage tables. The template is altered to remove the functionality to save to
storage. This script is useful to check the initial world is correctly loaded.
