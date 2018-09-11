from orator.migrations import Migration


class AddFullyQualifiedSources(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('fqs') as table:
            table.increments('id').unsigned()
            table.text('url').unique()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.datetime('next_update')
            table.integer('update_interval')
            table.integer('feed_id').unsigned()
            table.foreign('feed_id').references('id').on('feeds').ondelete('cascade')

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop_if_exists('fqs')
