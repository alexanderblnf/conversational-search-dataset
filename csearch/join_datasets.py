from csearch.converters.xml2pandas import XML2Pandas
import pandas as pd

# Generate the dataframe for posts and comments
posts_df = XML2Pandas('../stackexchange_dump/Posts.xml').convert()
comments_df = XML2Pandas('../stackexchange_dump/Comments.xml').convert()
votes_df = XML2Pandas('../stackexchange_dump/Comments.xml').convert()

# Filter votes to get only approved ones
votes_df = votes_df.loc[votes_df['VoteTypeId'] == '1']

# Join the dataframes into one
posts_comments_df = posts_df.merge(
    comments_df,
    how='left',
    left_on='Id',
    right_on='PostId',
    suffixes=('_post', '_comment')
)
final_df = posts_comments_df.merge(
    votes_df,
    how='left',
    left_on='Id_post',
    right_on='PostId',
    suffixes=('_comments', '_votes')
)

