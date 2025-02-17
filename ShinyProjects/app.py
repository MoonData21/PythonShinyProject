from pathlib import Path
import pandas as pd
import calendar
import plotly.express as px
from shiny import reactive
from shiny.express import render, input, ui
from shinywidgets import render_plotly
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import folium
from folium.plugins import HeatMap

# cd ShinyProjects rsconnect deploy shiny path/to/your/app --name moondata21 --title your-app-name .
# CSS styling
ui.tags.style(
    """
    .header-container {
        display: flex;
        align-items: center;
        justify-content: center; /* Centers the content horizontally */
        height: 60px;
    }

    .logo-container {
        margin-right: 5px; /* Adjust the spacing as needed */
        height: 100% !important;
        padding: 10px;
    }

    .logo-container img {
        height: 40px;
    }

    .title-container h2 {
        color: black;
        padding: 5px;
        margin: 0;
    }

    body {
        background-color: lightblue;
    }

    .modebar{
        display: none;

    }
    """
)

FONT_COLOR = "#4C78A8"
FONT_TYPE = "Arial"
# Styling for Charts
def style_plotly_chart(fig, yaxis_title):
    fig.update_layout(
        xaxis_title="",  # Remove x-axis label
        yaxis_title=yaxis_title,  # Change y-axis label
        plot_bgcolor="rgba(0,0,0,0)",  # Remove background color
        showlegend=False,  # Remove the legend
        coloraxis_showscale=False,
        font=dict(family="Arial", size=12, color=FONT_COLOR),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig

ui.page_opts(window_title="Electronics Store Sales Dashboard", fillable=False)
# A function that changes the color from blue to green
# @reactive.calc
# def color():
#     return "green" if input.bar_color() else "blue"

# Getting the sales dataset from the Data folder. 
@reactive.calc
def dat():
    infile = Path(__file__).parent / "data/sales.csv"
    df = pd.read_csv(infile)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.month_name()
    df['hour'] = df["order_date"].dt.hour
    df['value'] = df['quantity_ordered'] + df['price_each']
    return df
# Header container
with ui.div(class_="header-container"):
    #with ui.div(class_="logo-container"):
    with ui.div(class_="title-container"):
            ui.h2("Electronics Store Sales Dashboard - 2024")
        # @render.image
        # def image():
        #     here = Path(__file__).parent
        #     img = {"src": here / "images/shiny-logo.png"}
        #     return img


# First Graph with ui.card & sidebar.
with ui.card():  
    ui.card_header("Sales By City")

    with ui.layout_sidebar():  
        with ui.sidebar(bg="#f8f8f8", open='open', width="350px"):    
            ui.input_selectize(
                "city",
                "Select a City",
                [
                    "Dallas (TX)",
                    "Boston (MA)",
                    "Los Angeles (CA)",
                    "San Francisco (CA)",
                    "Seattle (WA)",
                    "Atlanta (GA)",
                    "New York City (NY)",
                    "Portland (OR)",
                    "Austin (TX)",
                    "Portland (ME)",
                ],
                multiple=True,
                selected="Dallas (TX)"
            )
    @render_plotly
    def sales_over_time():
        df = dat()
        # print(list(df.city.unique()))
        sales = df.groupby(["city", "month"])["quantity_ordered"].sum().reset_index()
        sales_by_city = sales[sales["city"].isin(input.city())]
        month_orders = calendar.month_name[1:]
        fig = px.bar(
            sales_by_city,
            x="month",
            y="quantity_ordered",
            category_orders={"month": month_orders},
        )
        # Apply custom styling
        fig = style_plotly_chart(fig, yaxis_title="Quantity Ordered")
        #fig.update_traces(marker_color=color())
        return fig

# The code above did:
# Group the data by city and month, then sum the quantities ordered
# Filter the sales data to only include the selected city
# Define the order of months
# with ui.card():
with ui.layout_column_wrap(width= 1/2):
    with ui.navset_card_underline(id="tab", footer= ui.input_numeric("n", "Number of Items", 10, min=0, max=50)):  
        with ui.nav_panel("Top Sellers"):
            @render_plotly
            def plot_topsellers():
                df = dat()
                top_sales = (
                df.groupby("product")["quantity_ordered"]
                    .sum()
                    .nlargest(input.n())
                    .reset_index()
                    )
                fig = px.bar(top_sales, x="product", y="quantity_ordered", color="quantity_ordered", color_continuous_scale="Blues",)
                #fig.update_traces(marker_color=color())
             # Apply the standardized style
                fig = style_plotly_chart(fig, "Quantity Ordered")

                return fig

        with ui.nav_panel("Top Sellers ($)"):
            
            @render_plotly
            def plot_topsellers_value():
                df = dat()
                top_sales = (
                df.groupby("product")["value"]
                    .sum()
                    .nlargest(input.n())
                    .reset_index()
                    )
                fig = px.bar(top_sales, x="product", y="value", color="value", color_continuous_scale="Blues",)
                #fig.update_traces(marker_color=color())
                # Apply the standardized style
                fig = style_plotly_chart(fig, "Total Sales ($)")
                return fig

        with ui.nav_panel("Lowest Seller"):
            @render_plotly
            def plot_lowestsellers():
                df = dat()
                top_sales = (
                df.groupby("product")["quantity_ordered"]
                    .sum()
                    .nsmallest(input.n())
                    .reset_index()
                    )
                fig = px.bar(top_sales, x="product", y="quantity_ordered", color="quantity_ordered", color_continuous_scale="Reds",)
                #fig.update_traces(marker_color=color())
                # Apply the standardized style
                fig = style_plotly_chart(fig, "Quantity Ordered")
                return fig

        with ui.nav_panel("Lowest Sellers ($)"):
             
            @render_plotly
            def plot_lowestsellers_value():
                df = dat()
                top_sales = (
                df.groupby("product")["value"]
                    .sum()
                    .nsmallest(input.n())
                    .reset_index()
                    )
                fig = px.bar(top_sales, x="product", y="value", color="value", color_continuous_scale="Reds",)
                 #fig.update_traces(marker_color=color())
                 # Apply the standardized style
                fig = style_plotly_chart(fig, "Total Sales ($)")
                return fig
    
    with ui.card():
        ui.card_header("Sales By Time of Day Heatmap")
        @render.plot
        def plot_salesbytime():
            df = dat()
            sales_by_hour = df['hour'].value_counts().reindex(np.arange(0,24), fill_value=0)
            heatmap_data = sales_by_hour.values.reshape(24,1)
            sns.heatmap(heatmap_data,
                        annot=True,
                        fmt="d",
                        cmap="Blues",
                        cbar=False,
                        xticklabels=[],
                        yticklabels=[f"{i}:00" for i in range(24)])
            
             # plt.title("Number of Orders by Hour of Day")
            plt.xlabel("Order Count", color=FONT_COLOR, fontname=FONT_TYPE)
            plt.ylabel("Hour of Day", color=FONT_COLOR, fontname=FONT_TYPE)

            # Change the tick label color and font
            plt.yticks(color=FONT_COLOR, fontname=FONT_TYPE)
            plt.xticks(color=FONT_COLOR, fontname=FONT_TYPE)


with ui.card():
    ui.card_header('Sales by Location Map')
    #Use render.ui to render HTML
    @render.ui
    def plot_us_heatmap():
        df = dat()

        heatmap_data = df[['lat','long','quantity_ordered']].values

        map = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
        HeatMap(heatmap_data).add_to(map)
        return map

# correctly format the file by tying black app.py
# highlight the code and press tab for indenting.
# reset_index() populates the header with the column name.

with ui.card():
    ui.card_header("Sample Sales Data")

    @render.data_frame
    def sample_sales_data():
        return render.DataTable(dat().head(100), filters=True)

# ui.input_checkbox("bar_color", "Make Bars Green", False)
# highlight everything and press command/Ctrl forward slash to comment out blocks of code.