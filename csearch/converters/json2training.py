class JSON2Training:
    def __init__(self, json_data: dict):
        self.json_data = json_data
        self.__training_set = []

    def __process_dialogue(self, key: str, dialogue: dict) -> None:
        utterances = dialogue['utterances']
        user_utterances = list(
            filter(
                lambda utterance: utterance['actor_type'] == 'user', utterances
            )
        )

        for user_utterance in user_utterances:
            current_pos = user_utterance['utterance_pos']
            if current_pos == len(utterances):
                break

            first_utterance_pos = max(1, current_pos - 10)
            training_entry = ([key] + [utterance['utterance'] for utterance in utterances
                                       if first_utterance_pos <= utterance['utterance_pos'] <= current_pos + 1])

            self.__training_set.append(training_entry)

    def convert(self) -> list:
        for (key, dialogue) in self.json_data.items():
            self.__process_dialogue(key, dialogue)

        return self.__training_set

