from orator.migrations import Migration


class AddFullTextSearch(Migration):
    def up(self):
        """
        Run the migrations.
        """
        conn = self.schema.get_connection()
        conn.statement(
            str(
                conn.raw(
                    "ALTER TABLE links ADD COLUMN textsearchable_title tsvector; UPDATE links SET textsearchable_title = to_tsvector('english', title);"
                )
            )
        )
        conn.statement(
            str(
                conn.raw(
                    "ALTER TABLE links ADD COLUMN textsearchable_text tsvector; UPDATE links SET textsearchable_text = to_tsvector('english', text);"
                )
            )
        )
        conn.statement(
            str(
                conn.raw(
                    "CREATE OR REPLACE FUNCTION link_create_tsvectors()   \n"
                    "RETURNS TRIGGER AS $$\n"
                    "BEGIN\n"
                    "    NEW.textsearchable_title = to_tsvector('english', NEW.title);\n"
                    "    NEW.textsearchable_text = to_tsvector('english', NEW.text);\n"
                    "    RETURN NEW;\n"
                    "END;\n"
                    "$$ language 'plpgsql';"
                )
            )
        )
        conn.statement(
            str(
                conn.raw(
                    "CREATE TRIGGER update_link_tsvectors BEFORE INSERT OR UPDATE ON links FOR EACH ROW EXECUTE PROCEDURE link_create_tsvectors();"
                )
            )
        )
        conn.statement(
            str(
                conn.raw(
                    "CREATE INDEX textsearchable_text_idx ON links USING GIN (textsearchable_text);  "
                )
            )
        )
        conn.statement(
            str(
                conn.raw(
                    "CREATE INDEX textsearchable_title_idx ON links USING GIN (textsearchable_title);  "
                )
            )
        )

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table("links") as table:
            table.drop_column("textsearchable_title", "textsearchable_text")
        conn = self.schema.get_connection()
        conn.statement(str(conn.raw("DROP TRIGGER update_link_tsvectors ON links")))
