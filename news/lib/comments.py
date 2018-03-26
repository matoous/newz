def add_new_comment(link, comment):
    from news.models.link import Link
    Link.where('id', link.id).increment('comments_count')
    from news.models.comment import CommentTree, SortedComments
    CommentTree.add(link, comment)
    SortedComments.update(link, comment)


def update_comment(comment):
    from news.models.comment import SortedComments, Comment
    comment = Comment.update_cache(comment) # we need to updated sorted comments with the UPDATED COMMENT
    # spend some time before debugging this, because I still had the old unupdated comment
    SortedComments.update(comment.link, comment)
