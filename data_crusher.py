import pandas as pd
import sqlite3

def clean_data():
    # Load raw data
    atlas = pd.read_csv("data/raw_atlas.csv")
    border = pd.read_csv("data/raw_border.csv")

    # Clean Atlas data
    atlas_clean = atlas[["City", "State", "Technology", "Vendor"]].dropna()
    
    # Clean Border data
    border_clean = border[["City", "State", "Technology Type", "Vendor"]]
    border_clean = border_clean.rename(columns={"Technology Type": "Technology"})
    
    # Save cleaned data
    atlas_clean.to_csv("data/processed/atlas_clean.csv", index=False)
    border_clean.to_csv("data/processed/border_clean.csv", index=False)
    
    # Load into SQLite
    conn = sqlite3.connect('data/surveillance.db')
    atlas_clean.to_sql('atlas_data', conn, if_exists='replace', index=False)
    border_clean.to_sql('border_data', conn, if_exists='replace', index=False)
    conn.close()

if __name__ == '__main__':
    clean_data()