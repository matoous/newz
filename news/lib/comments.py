

def add_new_comment(link, comment):
    from news.models.link import Link
    Link.where('id', link.id).increment('comments_count')
    from news.models.comment import CommentTree
    CommentTree.add(link, comment)
    from news.models.comment import SortedComments
    SortedComments.update(link, comment)