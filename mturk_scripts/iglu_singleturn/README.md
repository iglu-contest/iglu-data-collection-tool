# Single turn data collection for Iglu using Mturk

This directory contains the scripts used to automatically generate and validate Mturk hits for single-turn data collection.

## Usage

After completing the setup, run the script `run_data_collection.py` to create new Mturk HITs and listen for completed assignments.

Usage:

```bash
$ python .\run_data_collection.py --hit_count 2 \
        --template_filepath .\templates\builder_normal.xml \
        --config sandbox
```

The steps executed are:

1. Search in a previous multiturn dataset for random `hit_count` starting worlds.
2. Create a new Turn for the selected starting world. A Turn is an abstraction that links the starting world paths with a new turn id, and eventually the paths to the collected data. Use the sandbox or requester environment according to the `config` parameter.
2. Create and publish HIT for the new turn by rendering the XML template in `template_filepath`. The HIT layout pulls a the javascript code that renders the game in a Voxelworld when the HIT is started. The same script keeps track of the movements of the agent, controlled by the annotator, and the changes in the world. These records are sent to Azure Storage when the HIT is submitted.
3. Store the Turn in an Azure Table.
3. Once a new submission is detected through the boto3 API, review the assignment as valid or not and deletes it.
4. Retrieve the Turn from Azure that was linked to the assignment and updates its information with the data received through the HIT in the previous step.

The script runs until there are no more open hits, i.e., hits that are not expired and that
are not already reviewed. It can be terminated prematurely with a kill signal,
in which case the previously open hit will not be closed and will eventually expire. New submitted assignments can be retrieved and approved if the script is executed again, before the assignment is auto approved or the hit expires.

## Set up

### API keys and credentials

Before starting the collection, it is necessary to have:
1. A valid Mturk account
2. An online storage where the game data collected in the HIT will be saved, sent directly from a javascript script included in the HIT.
3. Any storage to save the output of the HIT assignments, such as utterances or game metadata.

In this implementation, Azure Blob Storage is used as a solution for point 2., and Azure Tables for point 3, but the tool can be adapted for other resources as well. The Data Storage section explains the data format in more details.

To set up the Azure and Mturk credentials, copy the file `.env.template` and replace the corresponding variables.

```bash
# API keys obtained from AWS console
AWS_ACCESS_KEY_ID=<YOUR_KEY>
AWS_SECRET_ACCESS_KEY=<YOUR_KEY>

# Azure credentials obtained from Azure portal. They must have list, read and write permissions for
# tables and blobs.
AZURE_STORAGE_CONNECTION_STRING=<STORAGE_CONNECTION_STRING>
AZURE_STORAGE_SAS=<STORAGE_CONNECTION_STRING>
```

### Environment

Once the keys have been correctly set, create an environment with the tool of your choice and install the dependencies in `requirements.txt`. Example:

bash
```
$ conda create --name iglu_dataset python=3.9
$ conda activate iglu_dataset
$ pip install -r .\requirements.txt
```

### HIT configuration

The HIT involves two parts: the metadata, such as title, keywords, reward, expiration, etc., and the layout.

To separate the HIT definition from the execution code, most of the HIT metadata is placed in the `env_configs.json` file. Update these files directly to change the parameters that will be passed to the boto3 client hit creation method.

Additionally, a RequesterAnnotation field is added to keep track of the type of hit (builder-normal, clarifying-question, etc). This optimizes the search for open hits and allows to run multiple data collection projects concurrently.

TODO Add more documentation on the layout template.

## Data format and storage

Game data is composed of four types of data: game metadata (game id, turn id, etc.), utterances, world description and sequence of player's actions. Game metadata and utterances are stored in Azure tables,
while the world and player's actions are stored in json files in Azure containers.

The initial structures are random turns of previous games, and share the same format as the end structures. The end structure of a turn is read from the turn json file and taken as initial structure of the next turn.

TODO Azure table description

TODO Azure Storage containers description

## Testing

* Unittest normal scripts that mock all elements and do not require real credentials.
* Ping scripts that read from resources using real credentials.
* Creation of test hits in sandbox: the script will only create the hit, without updating any
value in the storage tables. The template is altered to remove the functionality to save to
storage. This script is useful to check the initial world is correctly loaded.
