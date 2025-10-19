from culture_dataset import *
from daily_routine import *
from family_dataset import *
from health_dataset import *
from nostalgia_dataset import *
import pandas as pd
from datasets import load_dataset

combined_data = elderly_culture_daily + daily_routine + family + healthcare + nostalgia
combined_df = pd.DataFrame(combined_data)
combined_df.columns = ["singlish", "english"]

gab_df = pd.DataFrame(load_dataset("gabrielchua/singlish-to-english-synthetic")["train"])
gab_df.drop(columns = ["index"], inplace = True)

final_df = pd.concat([gab_df, combined_df], axis = 0)
print(final_df.iloc[-1])