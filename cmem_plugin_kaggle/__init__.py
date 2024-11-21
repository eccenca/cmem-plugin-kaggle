"""cmem-plugin-kaggle"""

import os

# Importing the Kaggle module initializes KaggleApi, which fails if the required environment
# variables or kaggle.json are missing in the config folder. To prevent this,
# we are setting the Kaggle environment to empty.
if "KAGGLE_USERNAME" not in os.environ:
    os.environ["KAGGLE_USERNAME"] = ""
    os.environ["KAGGLE_KEY"] = ""
