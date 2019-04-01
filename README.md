# conversational-search-dataset
This repo contains the implementation for obtaining a conversational search dataset

To fetch the initial [stackExchange dump](https://archive.org/details/stackexchange),
you need to run the `fetch_stackexchange_dump.sh` script. This will create a folder
called `stackexchange_dump` and will put all the .xml files there. During the process, it might ask
to install a utility to unzip `.7z` files. 

To run the script that turns the XML dump into a JSON file similar to
[this format](https://ciir.cs.umass.edu/downloads/msdialog/), you need to run
`run.py`. The output is stored in `stackexchange_dump/data.json`

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