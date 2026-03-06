import pandas as pd

df = pd.read_excel("dummy_patch_servers.xlsx")
filtered_df = df[df["Application Name"].str.contains("lyric", case=False, na=False)]
server_list = filtered_df.to_dict(orient="records")
print(server_list)