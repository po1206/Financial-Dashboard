import dash
import dash_core_components as dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.subplots as ms
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta
import dash_html_components as html

#Import the Finnhub API connector from another Github repo
from finnhub_connector import FinnhubConnector

#define your API connector object that will later be used within the function
api_key = input('Paste your Finnhub API key: ')
connector = FinnhubConnector(api_key = api_key)

def run_dash_app(symbol):
    
    #Use the get_basic_financials method to get the data frame
    basic_fin = connector.get_basic_financials(symbol)
    
    #Change column names in the symbol[past_year] data frame to prettify for visualization
    columns = {'bookValue': 'Book Value (USD)',
    'cashRatio': 'Cash Ratio',
    'currentRatio': 'Current Ratio',
    'ebitPerShare': 'EBIT per Share (USD)',
    'eps': 'Earnings per Share (USD)',
    'ev': 'Embedded Value (USD)',
    'fcfMargin': 'Free Cash Flow Margin (USD)',
    'fcfPerShareTTM': 'Free Cash Flow Per Share (USD)',
    'grossMargin': 'Gross Margin (%)',
    'longtermDebtTotalAsset': 'Long Term Debt Total Asset (%)',
    'longtermDebtTotalCapital': 'Long Term Debt Total Capital (USD)',
    'longtermDebtTotalEquity': 'Long Term Debt Total Equity (USD)',
    'netDebtToTotalCapital': 'Net Debt to Total Capital',
    'netDebtToTotalEquity': 'Net Debt to Total Equity',
    'netMargin': 'Net Margin (%)',
    'operatingMargin': 'Operating Margin (%)',
    'pb': 'Price-to-Book Ratio',
    'peTTM': 'Price to Earnings TTM',
    'pfcfTTM': 'Price to Free Cash Flow TTM',
    'pretaxMargin': 'Pre-tax Margin (USD)',
    'psTTM': 'Price to Sales TTM',
    'quickRatio': 'Quick Ratio',
    'roaTTM': 'Return on Assets (USD)',
    'roeTTM': 'Return on Equity (USD)',
    'roicTTM': 'Return on Invested Capital (USD)',
    'rotcTTM': 'Return on Traded Capital (USD)',
    'salesPerShare': 'Sales per Share',
    'sgaToSale': 'SG&A to Sale',
    'totalDebtToEquity': 'Total Debt to Equity',
    'totalDebtToTotalAsset': 'Total Debt to Total Asset',
    'totalDebtToTotalCapital': 'Total Debt to Total Capital',
    'totalRatio': 'Total Ratio'}

    #Define annual and quarterly data frames from the dictionary output
    df_annual = basic_fin['annual']
    df_annual.rename(columns=columns, inplace=True)
    df_quarterly = basic_fin['quarterly']
    df_quarterly.rename(columns=columns, inplace=True)

    #Write a recursive helper function to normalize each value within (negative) 5 to 100 range to fit on the graph.
    #Keep track of the number of recursive calls made in order to know what was the original value.
    def normalize(x, count=1):
        if x>100 or x<-100:
            return normalize(x/10, count*10)
        elif -5<x<5:
            return normalize(x*10, count/10)
        elif count>1:
            return [round(x, 3), f'(Divided by {int(count)})']
        elif count<1:
            return [round(x, 3), f'(Multiplied by {int(1/count)})']
        else:
            return x

    #Define the past_year data frame and normalize the values using the above function
    df_pastyear = basic_fin['past_year']
    df_pastyear['normalized'] = df_pastyear['metric'].apply(lambda x: normalize(x) if (type(x)== float or type(x)== int) else x)
    
    #Get the high and low date for a stock as they are in the datetime format and cannot be normalized
    highdate = df_pastyear['metric']['52WeekHighDate']
    lowdate = df_pastyear['metric']['52WeekLowDate']
    
    #Create a new column for the normalized values to make them look like: X (multiplied/divided by x)
    df_pastyear['new'] = df_pastyear.index + ' ' + df_pastyear['normalized'].apply(lambda x: x[1] if type(x)==list else '')
    
    #Concatenate the columns and create final values, annotate the date with the 52 week low/high values
    df_pastyear['normalized_vals'] = df_pastyear['normalized'].apply(lambda x: x[0] if type(x)==list else x)
    dfs = df_pastyear.drop(['52WeekHighDate','52WeekLowDate'], axis=0)
    
    #Create the plotly go figure, make it horizontal for better representation
    fig = go.Figure(
        data=[go.Bar(x= dfs['normalized_vals'], y=dfs['new'])],
        layout_title=f"{symbol} Basic Stock Info")
    fig.layout.template='plotly_dark'
    fig.layout.height = 3500
    fig.update_layout(xaxis_title="Normalized value between (-)(5 to 100)", title_x=0.5, font=dict(size=15))
    fig.update_traces(marker_color='yellowgreen', orientation='h')
    fig.add_annotation(x=dfs['normalized_vals']['52WeekHigh']+10, y=4,
                       text=highdate,
                       showarrow=False,)
    fig.add_annotation(x=dfs['normalized_vals']['52WeekLow']+10, y=5,
                text=lowdate,
                showarrow=False,)

    #Define a list of dictionaries to create column options for dropdown menu on our annual and quarterly graphs
    a_and_q_options = [
                    {'label': 'Book Value (USD)', 'value': 'Book Value (USD)'},
                    {'label': 'Cash Ratio', 'value': 'Cash Ratio'},
                    {'label': 'Current Ratio', 'value': 'Current Ratio'},
                    {'label': 'EBIT per Share (USD)', 'value': 'EBIT per Share (USD)'},
                    {'label': 'Earnings per Share (USD)', 'value': 'Earnings per Share (USD)'},   
                    {'label': 'Embedded Value (USD)', 'value': 'Embedded Value (USD)'},
                    {'label': 'Free Cash Flow Margin (USD)', 'value': 'Free Cash Flow Margin (USD)'},
                    {'label': 'Free Cash Flow Per Share (USD)', 'value': 'Free Cash Flow Per Share (USD)'},
                    {'label': 'Gross Margin (%)', 'value': 'Gross Margin (%)'},
                    {'label': 'Long Term Debt Total Asset (%)', 'value': 'Long Term Debt Total Asset (%)'},
                    {'label': 'Long Term Debt Total Capital (USD)', 'value': 'Long Term Debt Total Capital (USD)'},
                    {'label': 'Long Term Debt Total Equity (USD)', 'value': 'Long Term Debt Total Equity (USD)'},
                    {'label': 'Net Debt to Total Capital', 'value': 'Net Debt to Total Capital'},
                    {'label': 'Net Debt to Total Equity', 'value': 'Net Debt to Total Equity'},
                    {'label': 'Net Margin (%)', 'value': 'Net Margin (%)'},
                    {'label': 'Operating Margin (%)', 'value': 'Operating Margin (%)'},
                    {'label': 'Price-to-Book Ratio', 'value': 'Price-to-Book Ratio'},
                    {'label': 'Price to Earnings TTM', 'value': 'Price to Earnings TTM'},
                    {'label': 'Price to Free Cash Flow TTM', 'value': 'Price to Free Cash Flow TTM'},
                    {'label': 'Pre-tax Margin (USD)', 'value': 'Pre-tax Margin (USD)'},
                    {'label': 'Price to Sales TTM', 'value': 'Price to Sales TTM'},
                    {'label': 'Quick Ratio', 'value': 'Quick Ratio'},
                    {'label': 'Return on Assets (USD)', 'value': 'Return on Assets (USD)'},
                    {'label': 'Return on Equity (USD)', 'value': 'Return on Equity (USD)'},
                    {'label': 'Return on Invested Capital (USD)', 'value': 'Return on Invested Capital (USD)'},
                    {'label': 'Return on Traded Capital (USD)', 'value': 'Return on Traded Capital (USD)'},
                    {'label': 'Sales per Share', 'value': 'Sales per Share'},
                    {'label': 'SG&A to Sale', 'value': 'SG&A to Sale'},
                    {'label': 'Total Debt to Equity', 'value': 'Total Debt to Equity'},
                    {'label': 'Total Debt to Total Asset', 'value': 'Total Debt to Total Asset'},
                    {'label': 'Total Debt to Total Capital', 'value': 'Total Debt to Total Capital'},
                    {'label': 'Total Ratio', 'value': 'Total Ratio'},
    ]
    
    #Create a grouped bar graph with earnings surprises (predicted and actual)
    df = connector.get_earnings_surprises(symbol)
    df['formatted'] = df.index
    df['formatted'] = df['formatted'].apply(lambda x: str(f'({x})'))
    df['Quarter'] = df['Quarter'].apply(lambda x: str(x))
    df['labels'] = df['Quarter']+ '  ' +df['formatted']
    fig2 = go.Figure(
        data=[
            go.Bar(
                name="Predicted",
                x=df['labels'],
                y=df['Estimate'],
                offsetgroup=0,
            ),
            go.Bar(
                name="Actual",
                x=df['labels'],
                y=df['Actual'],
                offsetgroup=1,
            ),
        ],
        layout=go.Layout(
            title=f"{symbol} Earnings Surprises",
            xaxis_title = "Quarter",
            yaxis_title="Value (USD)",
        )
    )
    fig2.layout.template='plotly_dark'
    fig2.data[0].marker.color = ('skyblue')
    fig2.data[1].marker.color = ('tomato')
    fig2.update_layout(title_x=0.5, font=dict(size=15))

    #Create a data frame for the current quote of our stock
    df_quote = connector.get_current_quote(symbol)
    fig3 = go.Figure(data=[go.Table(
        header=dict(values=df_quote.columns,
                    align='center',
                    line_color='black',
                    fill_color='ivory'),
        cells=dict(values=[i for i in list(df_quote.iloc[0])],
                   line_color='black',
                   fill_color='cyan',
                   align='center'))
    ])
    
    fig3.layout.template='plotly_dark'
    fig3.update_layout(width=1669, height=400,
        title=f"{symbol} Current Quote",
        title_x=0.5,
        title_font_color="white",
        title_font_size = 22,     
        font=dict(size=20, color='black'))
    
    #Define todays date and variables for dating back 3 years, a month, a week, and the last business day,
    #Which will later be used for cnadlestick charts
    current_date = date.today()
    threeyearsago = current_date - relativedelta(years=3)
    amonthago = current_date - relativedelta(months=1)
    aweekago = current_date - relativedelta(weeks=1)
    diff = max(1, (current_date.weekday() + 6) % 7 - 3)  
    lastweekday = current_date - relativedelta(days=diff)
    current_date = str(current_date)
    threeyearsago = str(threeyearsago)
    amonthago = str(amonthago)
    aweekago = str(aweekago)
    lastweekday = str(lastweekday)
    
    #Define data frames for candlestick charts
    df_threeyearsago = connector.get_stock_candles(symbol, 'D', threeyearsago, current_date)
    df_fifteen = connector.get_stock_candles(symbol, '15', amonthago, current_date)
    df_five = connector.get_stock_candles(symbol, '5', aweekago, current_date)
    df_one = connector.get_stock_candles(symbol, '1', lastweekday, current_date)

    #DASH APP STARTS
    app = dash.Dash(__name__)
    app.layout = html.Div(children=[
        html.H1(children=f'Interactive Financial Dashboard - {symbol}', style={'text-align': 'center'}),

        html.Div([
            html.Label(['Choose a Timeframe:'],style={'font-weight': 'bold'}),
            dcc.Dropdown(
                id='dropdown0',
                
                #Dropdown menu for being able to pick graphs with different time frames
                options=[
                    {'label': 'Three years to date (Daily)', 'value': 'Three years to date (Daily)'},
                    {'label': 'One month to date (15 min)', 'value': 'One month to date (15 min)'},
                    {'label': 'One week to date (5 min)', 'value': 'One week to date (5 min)'},
                    {'label': 'Last trading day (1 min)', 'value': 'Last trading day (1 min)'},
                        ],
                value='Three years to date (Daily)',
                style={"width": "60%"}),

        html.Div(dcc.Graph(id='graph0')),
            ]),
        
        #Define two dropdown menus with callbacks for our annual and quarterly data
        html.Div([
            html.Label(['Choose a Parameter:'],style={'font-weight': 'bold'}),
            dcc.Dropdown(
                id='dropdown',
                options= a_and_q_options,
                value='Book Value (USD)',
                style={"width": "60%"}),
            
        html.Div(dcc.Graph(id='graph')),        
            ]),
        html.Div([
            html.Label(['Choose a Parameter:'],style={'font-weight': 'bold'}),
            dcc.Dropdown(
                id='dropdown2',
                options= a_and_q_options,
                value='Book Value (USD)',
                style={"width": "60%"}),

        html.Div(dcc.Graph(id='graph2')),        
            ]),
        
        #Add all the figures defined before
        dcc.Graph(figure=fig),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig3),
    ])

    #Define callback functions for dropdown graphs
    @app.callback(
        Output('graph0', 'figure'),
        [Input(component_id='dropdown0', component_property='value')]
    )

    def select_graph(value):
        if value == 'Three years to date (Daily)':
            df=df_threeyearsago

        elif value == 'One month to date (15 min)':
            df=df_fifteen

        elif value == 'One week to date (5 min)':
            df = df_five

        elif value == 'Last trading day (1 min)':
            df = df_one

        #For each value make a plot with a subplot for Volume
        fig = ms.make_subplots(rows=2,
        cols=1, row_heights = [0.8, 0.2],
        shared_xaxes=True,
        vertical_spacing=0.02)
        fig.add_trace(go.Candlestick(x = df.index,
        name="Candles",
        low = df['Low'],
        high = df['High'],
        close = df['Close'],
        open = df['Open'],
        increasing_line_color = 'limegreen',
        decreasing_line_color = 'orangered'),
        row=1,
        col=1),

        #Add Volume Chart to Row 2 of subplot
        fig.add_trace(go.Bar(x=df.index,
        name="Volume",
        y=df['Volume'],
        marker_color='aqua'),
        row=2,
        col=1),

        #CODE BELOW: There are gaps in the candlestick chart which could be fixed by using rangebreaks. However, when applied
        #in conjunction with the dropdown option on graphs they cause an overlap of candles when toggling between graphs.
        #Feel free and try to uncomment this section and see what happens. It looks like someone already had this problem a
        #few years ago and the error needs to be fixed within the Plotly documentation. Without uncommenting the code will 
        #simply get displayed without rangebreaks.

#         fig.update_xaxes(
#                 rangeslider_visible=True,
#                 rangebreaks=[
#                     # NOTE: Below values are bound (not single values), ie. hide x to y
#                     dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
#                     dict(bounds=[16, 9.5], pattern="hour"),  # hide hours outside of 9.30am-4pm
#                 ]
#             )

        fig.update_layout(title = f'{symbol} {value} Candlestick Chart with Volume', title_x=0.5, height = 800, font=dict(size=15),
        yaxis1_title = 'Stock Price (USD)',
        yaxis2_title = 'Volume (M)',
        xaxis2_title = 'Datetime Range',
        xaxis1_rangeslider_visible = False,
        xaxis2_rangeslider_visible = True),
        fig.layout.template='plotly_dark'
        return fig

    #Callbacks for annual and quarterly graphs
    @app.callback(
        Output('graph', 'figure'),
        [Input(component_id='dropdown', component_property='value')]
    )
    def select_graph(value):
        fig = go.Figure(
            data=[go.Bar(x= df_annual.index, y=list(df_annual[f'{value}']))],
            layout_title=f"{symbol} Annual {value}"
        )
        fig.layout.template='plotly_dark'
        fig.update_layout(xaxis_title="Period", title_x=0.5, font=dict(size=15))
        fig.update_traces(marker_color='lightgreen')
        return fig

    @app.callback(
        Output('graph2', 'figure'),
        [Input(component_id='dropdown2', component_property='value')]
    )
    def select_graph2(value2):
        fig = go.Figure(
            data=[go.Bar(x= df_quarterly.index, y=list(df_quarterly[f'{value2}']))],
            layout_title=f"{symbol} Quarterly {value2}"
        )
        fig.layout.template='plotly_dark'
        fig.update_layout(xaxis_title="Period", title_x=0.5, font=dict(size=15))
        fig.update_traces(marker_color='orange')
        return fig

    #Run the app
    if __name__ == '__main__':
        app.run_server(debug=False)

symbol = input('Enter a stock symbol: ')
run_dash_app(symbol)
