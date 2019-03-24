from orator.migrations import Migration


class RemoveUniqueFqsRestriction(Migration):
    def up(self):
        """
        Run the migrations.
        """
        with self.schema.table("fqs") as table:
            table.drop_unique("fqs_url_unique")

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table("fqs") as table:
            table.unique("url")
