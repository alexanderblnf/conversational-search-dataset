from csearch.converters.xml2pandas import XML2Pandas
from csearch.converters.pandas2json import Pandas2JSON
import pandas as pd
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
        users_df = XML2Pandas(self.__root_folder + '/Users.xml').convert()
        spam_votes_df = votes_df.loc[votes_df['VoteTypeId'].isin(['4', '12'])].copy()

        # Convert necessary columns to numeric
        posts_df['Id'] = pd.to_numeric(posts_df['Id'])
        posts_df['OwnerUserId'] = pd.to_numeric(posts_df['OwnerUserId'])
        posts_df['ParentId'] = pd.to_numeric(posts_df['ParentId'])

        comments_df['Id'] = pd.to_numeric(comments_df['Id'])
        comments_df['PostId'] = pd.to_numeric(comments_df['PostId'])
        comments_df['UserId'] = pd.to_numeric(comments_df['UserId'])

        users_df['Id'] = pd.to_numeric(users_df['Id'])
        spam_votes_df['PostId'] = pd.to_numeric(spam_votes_df['PostId'])

        print('Merging the information...')
        posts_df = posts_df.loc[~posts_df['OwnerUserId'].isnull()]

        filtered_posts_df = pd.merge(
            posts_df,
            spam_votes_df,
            how='left',
            left_on='Id',
            right_on='PostId',
            suffixes=('_post', '_votes')
        )
        filtered_posts_df = filtered_posts_df.loc[filtered_posts_df['PostId'].isnull()]

        columns = ['AcceptedAnswerId', 'Body', 'CreationDate_post', 'Id_post', 'OwnerUserId', 'ParentId', 'PostTypeId',
                   'Score', 'Title']
        filtered_posts_df = filtered_posts_df[columns]

        posts_users_df = pd.merge(
            filtered_posts_df,
            users_df,
            how='left',
            left_on='OwnerUserId',
            right_on='Id',
            suffixes=('_post', '_user')
        )

        columns = ['AcceptedAnswerId', 'Body', 'CreationDate_post', 'Id_post', 'OwnerUserId', 'ParentId', 'PostTypeId',
                   'Score', 'Title', 'DisplayName']
        posts_users_df = posts_users_df[columns]

        comments_users_df = pd.merge(
            comments_df,
            users_df,
            how='left',
            left_on='UserId',
            right_on='Id',
            suffixes=('_comment', '_user')
        )

        columns = ['CreationDate_comment', 'Id_comment', 'PostId', 'Score', 'Text', 'UserId', 'DisplayName']
        comments_users_df = comments_users_df[columns]

        final_df = pd.merge(
            posts_users_df,
            comments_users_df,
            how='left',
            left_on='Id_post',
            right_on='PostId',
            suffixes=('_post', '_comment')
        )

        columns = ['AcceptedAnswerId', 'Body', 'CreationDate_post', 'Id_post', 'OwnerUserId', 'ParentId', 'PostTypeId',
                   'Score_post', 'Title', 'DisplayName_post', 'CreationDate_comment', 'Id_comment', 'Score_comment',
                   'Text', 'UserId', 'DisplayName_comment']
        filtered_df = final_df[columns]
        filtered_df = filtered_df.reset_index(drop=True)

        # Sort by post creation date and then by comment
        filtered_df = filtered_df.sort_values(by=['CreationDate_post', 'CreationDate_comment'])

        return filtered_df

    def build_json(self):
        df = self.__generate_dataframe()
        print('Starting the conversion to JSON format')
        df_json = Pandas2JSON(df, 'Apple').convert()

        with open(self.__root_folder + '/data.json', 'w') as fp:
            json.dump(df_json, fp)
