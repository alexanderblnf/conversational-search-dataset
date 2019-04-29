# conversational-search-dataset
This repo contains the implementation for obtaining a conversational search dataset

To fetch the initial [stackExchange dump](https://archive.org/details/stackexchange),
you need to run the `fetch_stackexchange_dump.sh` script. This will create a folder
called `stackexchange_dump` and will put all the .xml files there. During the process, it might ask
to install a utility to unzip `.7z` files. 

In order to install all the required external dependencies, please run pip install -r requirements.txt in the root folder of the project. 
We recommend using a virtual enviroment with Python 3.6.8.

To run the script that turns the XML dump into a JSON file similar to
[MSDialog - Complete](https://ciir.cs.umass.edu/downloads/msdialog/), you need to run
`python run.py json {topic}`, where `{topic}` is a supported topic from StackExchange.
The updated list of topics is being maintained
[here](https://github.com/alexanderblnf/conversational-search-dataset/wiki/Supported-Topics)
The output is stored in `stackexchange_dump/{topic}/data.json`

To run the script that turns the JSON file to a training dataset similar to 
[MSDialog - ResponseRank](https://ciir.cs.umass.edu/downloads/msdialog/), you need to run
`python run.py training {topic}`. 
The output is stored in `stackexchange_dump/{topic}/data_{allocation}.tsv`,
where `allocation` is either train, dev or test. 

There is also an utility script named `merge_topics.sh`, which accepts as many
topics as parameters. The script merges the `.tsv` files into one
(for each allocation) and provides a lookup file to identify which part of the
final file belongs to which topic.

Example: `./merge_topics bicycles movies` will create 1 file, found at 
`./stackexchange_dump/merge_bicycles_movies_{allocation}.tsv` that contains 
all the contexts from the 2 datasets. The `merge_bicycles_movies_{allocation}_lookup` file 
contains the positions at which each topic begins. 

##### JSON data format:

* __dialog_id__: a unique id for a dialog - ids are consecutive
* __category__: domain to which the dialogue belongs (for now, *Apple* is the only category)
* __title__: dialog title from the forum
* __dialog_time__: the time that the first utterance of the dialog was posted
* __utterances__: a list of utterances in this dialog
    * __actor_type__: *user* or *agent* (“user” refers to the information seeker that initiates the conversation. 
    All the other conversation participants are considered as “agents”)
    * __utterance_pos__: the utterance position in the dialog (starts from 1)
    * __utterance__: the content of the utterance
    * __votes__: number of votes the answer received from the community
    * __utterance_time__: the time that the utterance was posted
    * __is_answer__: whether the utterance is selected as the best answer by the community
    * __id__: the id of the original post/comment
     (for comments, the syntax is {post_id}_{comment_id})
     
##### Training dataset format:

__label \t utterance_1 \t utterance_2 ... \t final_response__

* __label__ is 1 when the final response is the true response, fetched from the
 actual conversation that occurred on StackExchange. Otherwise, it is 0 and it
 marks the fact that the __final_response__ is obtained using negative sampling
 via BM25. 
* The first utterance is always the initial question of the user
* The __final_response__ is always the response of the agent.  

