from orator.migrations import Migration


class AddFullTextSearchForFeeds(Migration):

    def up(self):
        """
        Run the migrations.
        """
        conn = self.schema.get_connection()
        conn.statement(str(conn.raw(
            "ALTER TABLE links ADD COLUMN textsearchable_name tsvector; UPDATE links SET textsearchable_name = to_tsvector('english', name);")))
        conn.statement(str(conn.raw(
            "ALTER TABLE links ADD COLUMN textsearchable_description tsvector; UPDATE links SET textsearchable_description = to_tsvector('english', description);")))
        conn.statement(str(conn.raw("CREATE OR REPLACE FUNCTION feed_create_tsvectors()   \n"
                                    "    RETURNS TRIGGER AS $$\n"
                                    "    BEGIN\n"
                                    "        NEW.textsearchable_name = to_tsvector('english', NEW.name);\n"
                                    "        NEW.textsearchable_description = to_tsvector('english', NEW.description);\n"
                                    "        RETURN NEW;\n"
                                    "    END;\n"
                                    "    $$ language 'plpgsql';")))
        conn.statement(str(conn.raw(
            "CREATE TRIGGER update_feed_tsvectors BEFORE INSERT OR UPDATE ON feeds FOR EACH ROW EXECUTE PROCEDURE feed_create_tsvectors();")))
        conn.statement(
            str(conn.raw("CREATE INDEX textsearchable_name_idx ON feeds USING GIN (textsearchable_name);  ")))
        conn.statement(
            str(conn.raw("CREATE INDEX textsearchable_description_idx ON feeds USING GIN (textsearchable_description);  ")))

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('feeds') as table:
            table.drop_column('textsearchable_name', 'textsearchable_description')
        conn = self.schema.get_connection()
        conn.statement(str(conn.raw("DROP TRIGGER update_feed_tsvectors ON links")))
