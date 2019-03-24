from orator.migrations import Migration


class AddSavedLinks(Migration):
    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create("saved_links") as table:
            table.big_integer("link_id").unsigned()
            table.integer("user_id").unsigned()
            table.datetime("created_at")
            table.datetime("updated_at")
            table.index("link_id")
            table.index("user_id")
            table.primary(["link_id", "user_id"])

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop_if_exists("saved_links")
