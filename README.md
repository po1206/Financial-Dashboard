## Instructions how to run the Financial Dash App:

1) Get a free Finnhub API key. https://github.com/dvasser/Finnhub-API-Connector has more information and will be used for the dash app.
2) Download this repository and navigate to the directory with all the files.
3) ```pip install -r requirements.txt```
4) Run the finn_dashapp.py (could run from the terminal/command line).
5) You will be prompted to paste your API key and the stock symbol you'd like to see the dashboard of. If you'd like, you can define your connector variable connector = FinnhubConnector(api_key = 'YOUR_API_KEY') at the top of the .py file and delete the line for the input. Then you simply have to click on the output link (port 8050) and explore the dash app. Read code comments for more details - (there is an error in Dash documentation which causes the x-minute candles to display with market closure breaks). Other than that, all the code works great. Enjoy!
