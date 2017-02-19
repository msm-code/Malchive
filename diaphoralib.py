import diaphora
import difflib

class Diaphora:
    def show_pseudo_diff(self, item):
        cur = self.db_cursor()
        sql = """select *
                 from (
                   select prototype, pseudocode, name, 1
                   from functions
                   where address = ?
                   and pseudocode is not null
                   union select prototype, pseudocode, name, 2
                   from diff.functions
                   where address = ?
                   and pseudocode is not null)
                order by 4 asc"""
        ea1 = str(int(item[1], 16))
        ea2 = str(int(item[3], 16))
        cur.execute(sql, (ea1, ea2))
        rows = cur.fetchall()
        if len(rows) != 2:
            Warning("Sorry, there is no pseudo-code available for either the first or the second database.")
        else:
            row1 = rows[0]
            row2 = rows[1]

            html_diff = difflib.HtmlDiff()
            buf1 = row1["prototype"] + "\n" + row1["pseudocode"]
            buf2 = row2["prototype"] + "\n" + row2["pseudocode"]
            src = html_diff.make_file(buf1.split("\n"), buf2.split("\n"))

            return src

        cur.close()

    bindiff = diaphora.CBinDiff('/home/msm/cryptomix/bb/decrypted0.mysqlite')
    bindiff.diff('/home/msm/cryptomix/bb/decrypted1.mysqlite')

    def do(group, items):
        for elm in items:
            id, off1, func1, off2, func2, sim, unk1, unk2, type = elm
            diff = show_pseudo_diff(bindiff, elm)
            open('{}_{}_vs_{}_with_{}.html'.format(group, off1, off2, sim), 'wb').write(diff)

    do('partial', bindiff.partial_chooser.items)
    do('unreliable', bindiff.unreliable_chooser.items)
