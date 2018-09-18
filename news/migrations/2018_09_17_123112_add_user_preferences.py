from orator.migrations import Migration


class AddUserPreferences(Migration):

    def up(self):
        """
        Run the migrations.
        """
        if not self.schema.has_column('users', 'p_infinite_scrolling'):
            with self.schema.table('users') as table:
                table.boolean('p_infinite_scrolling').default(True)
        if not self.schema.has_column('users', 'p_show_summaries'):
            with self.schema.table('users') as table:
                table.boolean('p_show_summaries').default(True)

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('users') as table:
            table.drop_column('p_infinite_scrolling', 'p_show_summaries')

