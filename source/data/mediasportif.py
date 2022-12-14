import pandas as pd
from bs4 import BeautifulSoup
import dateparser

from .scrap import get_data_from_url
from .scrap import RequestException


date_game_type_map = {
    "2018": {
        "1": ["2018-06-30", "2018-07-01", "2018-07-02", "2018-07-03"],
        "2": ["2018-07-06", "2018-07-07"],
        "3": ["2018-07-10", "2018-07-11"],
        "4": ["2018-07-14", "2018-07-15"]
    }
}

def get_matchs_data_from_url(url):
    ans = get_data_from_url(url)
        
    if ans.status_code != 200:
        raise RequestException(
            "Request response is not valid (status code %s)" % ans.status_code
        )

    html = BeautifulSoup(ans.text, "html.parser")

    fix_bug_2022 = False
    rows = []
    for line in html.find_all("tr"):
        content = [c.text.replace("\n", " ").strip() for c in line.find_all("td")]
        row = []
        # date
        if len(content) == 1:
            date_raw = content[0]
            if "–" in date_raw:
                
                if "JEUDI 1er NOVEMBRE" in date_raw:
                    fix_bug_2022 = True

                if fix_bug_2022:
                    date_raw = date_raw.replace("NOVEMBRE", "DECEMBRE")

                date, game_type = date_raw.split("–")
                date_ = str(dateparser.parse(date).date())
                date = date.split()
            else:
                date = date_raw.split()
                date_ = str(dateparser.parse(date_raw).date())
        
        # game details
        if len(content) == 6:
            game = content[1:]
            
            # if ratings not known
            if game[-1].startswith("X"):
                continue

            game[-1] = int(game[-1].replace(".", ""))

        else:
            continue

        if date[3] == "2018":

            game_type = "POULE"
            if date_ in date_game_type_map[date[3]]["1"]:
                game_type = "HUITIÈMES DE FINALE"
            elif date_ in date_game_type_map[date[3]]["2"]:
                game_type = "QUARTS DE FINALE"
            elif date_ in date_game_type_map[date[3]]["3"]:
                game_type = "DEMI-FINALE"
            elif date_ in date_game_type_map[date[3]]["4"]:
                game_type = "FINALE"

        elif date[3] == "2022":
            game_type = game_type.strip()
            if game_type.startswith("J"):
                game_type = "POULE"

        # handle when hour is empty
        if game[0] == "–":
            game[0] = rows[-1][6]
            
        row.append(date_)
        row.extend(date)
        row.append(game_type)
        row.extend(game)

        rows.append(row)

    cols = ["date", "day_of_week", "day", "month", "year", "game_type", "hour", "team_1", "team_2", "prct", "ratings"]
    game_ratings_df = pd.DataFrame(rows, columns=cols)
    game_ratings_df = game_ratings_df.groupby(cols[:-2]).agg(ratings=("ratings", "sum")).reset_index()

    return game_ratings_df