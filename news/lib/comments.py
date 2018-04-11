def add_new_comment(link, comment):
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
    CommentTree.add(link, comment)
    SortedComments.update(link, comment)


def update_comment(comment):
    """
    Updates comment and reorders comments if needed
    :param comment:
    """
    from news.models.comment import SortedComments
    SortedComments.update(comment.link, comment)
