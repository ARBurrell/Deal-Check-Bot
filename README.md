# Deal-Check-Bot
A bot for Discord that scrapes a chosen website for current deals. Currently designed for scraping Amazon Australia's latest 'top deal' specifically without using their affiliate API. Created mostly with Python 3.9, using Beautiful Soup, Selenium, Discord and Schedule packages. 


Using Deal Bot

Make sure the "config.toml" file has been populated with your Discord Bot Secret key. For automatic checking and updating, ensure you either have an "amazon-deals" text channel that the bot can access, or you've changed the value to DEAL_CHANNEL_NAME to the intended channel. For manual checks/updates, please use the "/deal" command. 

If you do not wish to have the bot run a check/post manually on startup each time, change the STARTUP_CHECK_ENABLED value to "False".

To personalise the bot's responses in the channel, edit the "deal_phrases.txt" and the "no_deal_phrases.txt" files. Each phrase should be on its own line. 


Things to note

- Keep Chrome open for the bot to continue working, closing Chrome will require you to restart the Python script. 
- Automated responses will only post if the deal has changed. Deal Bot will not acknowledge same deals when they're automatic, but will respond to /deal commands to let the channel know the deal has not changed. 


Hoping to add in the future

- Different Amazon regions support
- Different deal types, keyword deal searching, department-based deals
- Other website support (where API access is not available/limited)
