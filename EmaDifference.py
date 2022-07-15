import sqlite3 as sl

con = sl.connect('orders-executed.db')

with con:
    cur = con.cursor()

    # cur.execute("SELECT * FROM EMA_DIFFERENCE")
    # con.commit()
    # rows = cur.fetchall()

    cur.execute("SELECT * FROM RSI_STRATEGY")
    con.commit()
    rows = cur.fetchall()

    # cur.execute("SELECT * FROM ETHBUSD")
    # con.commit()
    # rows = cur.fetchall()

    # cur.execute("DELETE FROM ETHBUSD")

    for element in rows:
        print(element)

    # i = 1
    # for element in rows:
    #     if i>43:
    #         print(element[12])
    #     i +=1
