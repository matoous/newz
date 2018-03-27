def add_new_comment(link, comment):
    comment.link.incr('comments_count', 1)
    from news.models.comment import CommentTree, SortedComments
    CommentTree.add(link, comment)
    SortedComments.update(link, comment)


def update_comment(comment):
    from news.models.comment import SortedComments
    SortedComments.update(comment.link, comment)
