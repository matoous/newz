from orator.migrations import Migration


class AddUserPreferences(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.table('users') as table:
            if not table.has_column('p_infinite_scrolling'):
                table.boolean('p_infinite_scrolling').default(True)
            if not table.has_column('p_show_summaries'):
                table.boolean('p_show_summaries').default(True)

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('users') as table:
            table.drop_column('p_infinite_scrolling', 'p_show_summaries')

