# System overview

## Workflow

Q: 
- missing steps? 
- correct input/output?

Workflow steps from data to TAV:
- textfabric
  - input: corpus repo
  - output: watm
- untanngle 
  - input: watm
  - output: web annotations json, physical + logical segmented text json (uploaded to textrepo)
- annorepo indexer (also part of untanngle)
  - input: web annotations json
  - output: annorepo api
- brinta indexer
  - input: annorepo api 
  - output: es-index
- broccoli
  - input: annorepo api + es-index
  - output: es-index + broccoli api
- tav
  - input: broccoli (+ iiif-server: also part workflow?)

## Directories
How would our pipeline look on a virtual machine?
(First attempt...)

```md
- data/
  |-- workflow/ 
  |   |-- .git/
  |   |-- docker-compose-textfabric.yml # every step its own docker-compose setup, or one big yml?
  |   |-- docker-compose-untanngle.yml
  |   |-- docker-compose-brinta.yml
  |   |-- docker-compose-tav.yml
  |   \-- Makefile                      # every step a shell command/script?
  |-- projects/
  |   |-- suriano/
  |   |   |-- input/
  |   |   |   |-- .git/
  |   |   \-- output/
  |   |       |-- textfabric/
  |   |       |   |-- reports/
  |   |       |   |   |-- a.txt
  |   |       |   |   |-- b.csv
  |   |       |   |-- error.log
  |   |       |   \-- info.log
  |   |       |-- untanngle/
  |   |       \-- brinta/
  |   \-- vangogh/
  \-- site/
      |-- .git/
      |-- server.py
      |-- index.html
      \-- workflow.js
```

Q: How to link user input (via server.py) to the configuration of the workflow?
- Should there be any configuration in our first version?
- (Maybe a fully automatic pipeline without configuration is already quite a milestone?)

### Input
Q: How does each step know where to find the inputs from the previous step and where to put the outputs for the next service?
- maybe a wrapper for each step that knows what the default inputs and outputs are: it collects the input, and moves the output as needed ?

### Intermediate

### Output

## Configuration system

Yaml files at several levels of abstraction

## Logging

Loglevel is regulated per step.
Intention: only messages for end user are passed to the workflow system.

## Development process

### Code changes
Q: How to update code?
- Text fabric updates code by mounting changes in data repo in existing container
  - Can be pulled from repo and mounted by script?
- Next steps (AR, TR, Br, Tav) update code by providing new docker image
  - Can be updated manually in docker compose yml?

### Configuration changes

### Data changes

### Containers and images

Q: What is in a container and what is in volumes that are shared between containers?

