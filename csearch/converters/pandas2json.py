from math import floor
from pandas import DataFrame


class Pandas2JSON:
    """
    This class handles the conversion of a Pandas dataframe to a JSON dataset
    """

    def __init__(self, df: DataFrame, category: str):
        self.df = df
        self.category = category
        self.__output = {}
        self.__global_index = 0

    def __init_entry(self, utterance):
        """
        Format the standard entry before adding the utterances
        :param utterance:
        :return: An utterance "stub"
        """
        return {
            'category': self.category,
            'title': utterance['Title'],
            'dialog_time': utterance['CreationDate_post']
        }

    @classmethod
    def __get_usernames(cls, df):
        users_comments = df.loc[~df['DisplayName_comment'].isnull()].drop_duplicates('DisplayName_comment')[
            'DisplayName_comment'].tolist()
        users_posts = df.drop_duplicates('DisplayName_post')['DisplayName_post'].tolist()

        return users_comments + list(set(users_posts) - set(users_comments))

    @classmethod
    def __is_other_mention(cls, usernames, text):
        normalized_text = ''
        try:
            normalized_text = text[1:] if text[0] == '@' else text
        except IndexError:
            print(text)

        return normalized_text.startswith(usernames)

    @classmethod
    def __format_utterance(cls, utterance, current_position, is_agent=False, is_comment=False, is_accepted=False):
        """
        Given an utterance, this function formats it similar to this https://ciir.cs.umass.edu/downloads/msdialog/
        :param utterance: The current utterance to be formatted
        :param current_position: The position of the current utterance
        :param is_agent: True if the utterance has been emitted by an agent
        :param is_comment: True if the utterance is a comment
        :param is_accepted: True if the current response is the accepted one
        :return: A formatted utterance
        """

        actor_type = 'agent' if is_agent else 'user'
        if is_comment:
            return {
                'utterance': utterance['Text'],
                'utterance_time': utterance['CreationDate_comment'],
                'utterance_pos': current_position,
                'actor_type': actor_type,
                'user_name': utterance['DisplayName_comment'],
                'user_id': utterance['UserId'],
                'votes': utterance['Score_comment'],
                'id': utterance['Id_post'] + utterance['Id_comment'],
                'is_answer': 0
            }

        return {
            'utterance': utterance['Body'],
            'utterance_time': utterance['CreationDate_post'],
            'utterance_pos': current_position,
            'actor_type': actor_type,
            'user_name': utterance['DisplayName_post'],
            'user_id': utterance['OwnerUserId'],
            'votes': utterance['Score_post'],
            'id': utterance['Id_post'],
            'is_answer': 1 if is_accepted else 0
        }

    def __append_utterance(self, entry, original_post, response, usernames, is_accepted=False):
        """
        Appends the utterance(s) to the dialog
        :param entry: The dialogue entry to which the utterances are appended
        :param original_post: The original question
        :param response: The current response under analysis
        :param is_accepted: Is True if the current response is the accepted one
        :return: The updated dialogue entry
        """

        current_position = 1
        updated_entry = entry
        if 'utterances' not in updated_entry:
            updated_entry['utterances'] = []
            updated_entry['utterances'].append(self.__format_utterance(original_post, current_position))
            current_position += 1

            updated_entry['utterances'].append(
                self.__format_utterance(
                    response, current_position, is_agent=True, is_comment=False, is_accepted=is_accepted
                )
            )
            current_position += 1
        else:
            current_position = len(entry['utterances']) + 1

        if response['UserId'] == original_post['OwnerUserId'] and ~self.__is_other_mention(usernames, response['Text']):
            updated_entry['utterances'].append(
                self.__format_utterance(response, current_position, is_agent=False, is_comment=True)
            )
            current_position += 1

        if response['UserId'] == response['OwnerUserId'] and ~self.__is_other_mention(usernames, response['Text']):
            updated_entry['utterances'].append(
                self.__format_utterance(response, current_position, is_agent=True, is_comment=True)
            )

        return updated_entry

    def __generate_dialogues_from_responses(self, original_post, responses):
        """
        Given a question, this function processes all the responses and turns them into separate dialogues
        :param original_post: The original question on the thread
        :param responses: A list of all the responses
        :return:
        """
        if responses.shape[0] == 0:
            return

        user_username = original_post['DisplayName_post']
        usernames = tuple(set(self.__get_usernames(responses)) - set(user_username))

        current_post_id = responses.iloc[0]['Id_post']
        accepted_answer_id = original_post['AcceptedAnswerId']
        entry = self.__init_entry(original_post)
        for index, response in responses.iterrows():
            current_response_id = response['Id_post']
            is_accepted = (current_response_id == accepted_answer_id)
            if current_response_id == current_post_id:
                entry = self.__append_utterance(entry, original_post, response, usernames, is_accepted)
            else:
                self.__output[self.__global_index] = entry
                self.__global_index += 1
                entry = self.__init_entry(original_post)
                current_post_id = current_response_id
                entry = self.__append_utterance(entry, original_post, response, usernames, is_accepted)

        self.__output[self.__global_index] = entry
        self.__global_index += 1

    def convert(self):
        """
        Given a dataframe, this function turns it into a JSON array with dialogues and utterances
        :return: JSON dataset
        """
        original_posts_df = self.df.loc[self.df['PostTypeId'] == '1'].drop_duplicates('Id_post')
        original_posts_df = original_posts_df.reset_index(drop=True)

        responses_df = self.df.loc[
            (self.df['PostTypeId'] == '2') &
            (self.df['Text'].isnull() | (~self.df['Text'].isnull() & ~self.df['UserId'].isnull()))
        ]

        responses_df = responses_df.reset_index(drop=True)

        total_progress_increment = floor(original_posts_df.shape[0] / 100)

        for progress_index, original_post in original_posts_df.iterrows():
            if progress_index % total_progress_increment == 0:
                print('Progress: ' + str(floor(progress_index / total_progress_increment)) + '%')

            original_post_id = original_post['Id_post']
            responses_df_current = responses_df.loc[responses_df['ParentId'] == original_post_id]

            self.__generate_dialogues_from_responses(original_post, responses_df_current)

        return self.__output
