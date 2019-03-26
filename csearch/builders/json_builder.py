from csearch.converters.xml2pandas import XML2Pandas
from csearch.converters.pandas2json import Pandas2JSON
import json


class StackExchangeJSONBuilder:

    def __init__(self, folder):
        self.__root_folder = folder

    def __generate_dataframe(self):
        print('Fetching XML files from ' + self.__root_folder)
        # Generate the dataframe for posts and comments
        posts_df = XML2Pandas(self.__root_folder + '/Posts.xml').convert()
        comments_df = XML2Pandas(self.__root_folder + '/Comments.xml').convert()
        votes_df = XML2Pandas(self.__root_folder + '/Votes.xml').convert()
        spam_votes_df = votes_df.loc[votes_df['VoteTypeId'].isin(['4', '5'])]

        print('Merging the information...')
        posts_comments_df = posts_df.merge(
            comments_df,
            how='left',
            left_on='Id',
            right_on='PostId',
            suffixes=('_post', '_comment')
        )
        final_df = posts_comments_df.merge(
            spam_votes_df,
            how='left',
            left_on='Id_post',
            right_on='PostId',
            suffixes=('_comments', '_votes')
        )

        # Filter out spam posts
        final_df = final_df.loc[final_df['PostId_votes'].isnull()]

        required_columns = [
            'AcceptedAnswerId', 'AnswerCount', 'Body', 'CreationDate_post', 'CreationDate_comment',
            'FavoriteCount', 'Id_post', 'Id_comment', 'OwnerUserId', 'ParentId', 'PostTypeId',
            'Score_comment', 'Score_post', 'Tags', 'Text', 'Title', 'UserId_comments'
        ]

        # Leave only columns that are useful
        filtered_df = final_df[required_columns]
        filtered_df = filtered_df.reset_index()

        return filtered_df

    def build_json(self):
        df = self.__generate_dataframe()
        print('Starting the conversion to JSON format')
        df_json = Pandas2JSON(df, 'Apple').convert()

        with open(self.__root_folder + '/data.json', 'w') as fp:
            json.dump(df_json, fp)
