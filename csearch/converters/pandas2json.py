from math import floor
from pandas import DataFrame


class Pandas2JSON:

    def __init__(self, df: DataFrame, category: str):
        self.df = df
        self.category = category
        self.__output = {}
        self.__global_index = 0

    def __init_entry(self, utterance):
        return {
            'category': self.category,
            'title': utterance['Title'],
            'dialog_time': utterance['CreationDate_post']
        }

    @classmethod
    def __format_utterance(self, utterance, current_position, is_agent=False, is_comment=False):
        actor_type = 'agent' if is_agent else 'user'
        if is_comment:
            return {
                'utterance': utterance['Text'],
                'utterance_time': utterance['CreationDate_comment'],
                'utterance_pos': current_position,
                'actor_type': actor_type,
                'user_id': utterance['UserId_comments'],
                'votes': utterance['Score_comment']
            }

        return {
            'utterance': utterance['Body'],
            'utterance_time': utterance['CreationDate_post'],
            'utterance_pos': current_position,
            'actor_type': actor_type,
            'user_id': utterance['OwnerUserId'],
            'votes': utterance['Score_post']
        }

    def __append_utterance(self, entry, original_post, response):
        current_position = 1
        updated_entry = entry
        if 'utterances' not in updated_entry:
            updated_entry['utterances'] = []
            updated_entry['utterances'].append(self.__format_utterance(original_post, current_position))
            current_position += 1

            updated_entry['utterances'].append(self.__format_utterance(response, current_position, is_agent=True))
            current_position += 1
        else:
            current_position = len(entry['utterances']) + 1

        if response['UserId_comments'] == original_post['OwnerUserId']:
            updated_entry['utterances'].append(
                self.__format_utterance(response, current_position, is_agent=False, is_comment=True)
            )
            current_position += 1

        if response['UserId_comments'] == response['OwnerUserId']:
            updated_entry['utterances'].append(
                self.__format_utterance(response, current_position, is_agent=True, is_comment=True)
            )

        return updated_entry

    def __generate_dialogues_from_responses(self, original_post, responses):
        if responses.shape[0] > 0:
            current_post_id = responses.iloc[0]['Id_post']
            entry = self.__init_entry(original_post)
            for index, response in responses.iterrows():
                current_response_id = response['Id_post']
                if current_response_id == current_post_id:
                    entry = self.__append_utterance(entry, original_post, response)
                else:
                    self.__output[self.__global_index] = entry
                    self.__global_index += 1
                    entry = self.__init_entry(original_post)
                    current_post_id = current_response_id
                    entry = self.__append_utterance(entry, original_post, response)

            self.__output[self.__global_index] = entry
            self.__global_index += 1

    def convert(self):
        original_posts_df = self.df.loc[self.df['PostTypeId'] == '1'].drop_duplicates('Id_post')
        original_posts_df = original_posts_df.reset_index(drop=True)

        responses_df = self.df.loc[self.df['PostTypeId'] == '2']
        responses_df = responses_df.reset_index(drop=True)

        total_progress_increment = floor(original_posts_df.shape[0] / 100)

        for progress_index, original_post in original_posts_df.iterrows():
            if progress_index % total_progress_increment == 0:
                print('Progress: ' + str(floor(progress_index / total_progress_increment)) + '%')

            original_post_id = original_post['Id_post']
            responses_df_current = responses_df.loc[responses_df['ParentId'] == original_post_id].sort_values(
                by=['Id_post'])

            self.__generate_dialogues_from_responses(original_post, responses_df_current)

        return self.__output
