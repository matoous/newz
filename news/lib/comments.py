def add_new_comment(link_id, comment):
    """
    Adds new comment to given link
    Increment comment count
    Adds comment to comment tree
    Adds comment to sorted comments
    :param link: link
    :param comment: comment
    """
    comment.link.incr('comments_count', 1)
    from news.models.comment import CommentTree, SortedComments
    # insert new comment into the comment tree of given link
    CommentTree(link_id).add([comment])
    SortedComments(link_id, comment.parent_id).update([comment])


def update_comment(comment):
    """
    Updates comment and reorders comments if needed
    :param comment:
    """
    from news.models.comment import SortedComments
    SortedComments(comment.link_id, comment.parent_id).update([comment])
