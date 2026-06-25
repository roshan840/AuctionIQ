import sqlite3

def check():
    conn = sqlite3.connect('auctions.db')
    cursor = conn.cursor()
    
    total = cursor.execute("SELECT count(*) FROM properties").fetchone()[0]
    na_count = cursor.execute("SELECT count(*) FROM properties WHERE notice_image_url = 'N/A' OR notice_image_url IS NULL").fetchone()[0]
    
    print(f"Total: {total}")
    print(f"Missing URLs (N/A or NULL): {na_count}")
    
    samples = cursor.execute("SELECT notice_image_url FROM properties LIMIT 5").fetchall()
    print("Samples:", samples)
    
if __name__ == "__main__":
    check()
