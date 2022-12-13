![logo](banner.jpg)

HourAI - GPT2 AI conversational bot

Summary:

Modules needed:

  - requests@2.27.1
  - discord@1.7.3

Files present:

  - bot-discord.py - the main discord bot file
  - data_parser.js - used to parse the livedata.json into dataset.csv
  - datasets/ - stores data
    - dataset.csv - main dataset used for training
    - livedata.json - stored messages awaiting review
  - configs/ - configuration files
    - bot_configs/ - configuration files for the platform(s)
      - discord.json - configuration file for discord
      - telegram.json - configuration file for telegram
      - twitter.json - configuration file for twitter
    - model.json - configuration file for the model (used mainly by ShanghAI)
