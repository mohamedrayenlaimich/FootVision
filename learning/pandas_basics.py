import pandas as pd

players = {
    "player_id": [10, 7, 9],
    "team": ["A", "B", "A"],
    "speed": [31.5, 29.8, 30.7]
}

df = pd.DataFrame(players)

print(df)
print(df["team"])
print(df.head(2))
print(df.tail(1))
print(df.describe())
import pandas as pd

# Tracking data
data = {
    "player_id": [10, 10, 10, 7, 7, 7, 9, 9, 9],
    "team": ["A", "A", "A", "B", "B", "B", "A", "A", "A"],
    "speed": [30, 31, 32, 28, 29, 30, 29, 31, 30]
}

df = pd.DataFrame(data)

print("=== DATA ===")
print(df)

# 1. Average speed per player
print("\n=== AVERAGE SPEED PER PLAYER ===")
print(df.groupby("player_id")["speed"].mean())

# 2. Maximum speed per player
print("\n=== MAXIMUM SPEED PER PLAYER ===")
print(df.groupby("player_id")["speed"].max())

# 3. Minimum speed per player
print("\n=== MINIMUM SPEED PER PLAYER ===")
print(df.groupby("player_id")["speed"].min())

# 4. Average speed per team
print("\n=== AVERAGE SPEED PER TEAM ===")
print(df.groupby("team")["speed"].mean())