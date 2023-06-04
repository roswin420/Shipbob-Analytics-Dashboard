# import necessary libraries
from sqlalchemy import create_engine, text
from sqlalchemy.types import String, Integer, DateTime, Float

import pandas as pd 
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.echo_expander import echo_expander
from streamlit_extras.dataframe_explorer import dataframe_explorer

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots



#set page config
st.set_page_config(page_title="Supply Chain Analytics ", page_icon=None, layout="wide")


#Title and Logo
_left, mid, _right = st.columns(3)
with mid:
    col1, col2 = st.columns([1,3])
    with col1:
        st.image("https://logosandtypes.com/wp-content/uploads/2022/03/shipbob.svg",width=125)
    with col2:
        st.markdown("<h1 style='text-align: center; color: White;'>Shipbob Analytics Dashboard</h1>", unsafe_allow_html=True)

   



# MySQL parameters
username = 'root'
password = 'root'
host = 'localhost:3306'
database = 'shipbob'

# Setup connection string
mysql_conn_str = f'mysql+mysqlconnector://{username}:{password}@{host}/{database}'

# Create the connection engine object to establish connection to database
engine = create_engine(mysql_conn_str)

# Function to execute the query and retrive data from the 'shipbob' database
def execute_sql_query(query, engine):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df




# Set up the Streamlit layout

# Section 1

def industry_avg_monthly_revenue():
    st.title('Industry-wise Average Monthly Revenue')
    query = """
    WITH monthly_revenues AS (
        SELECT 
            u.Industry,
            MONTH(o.PurchaseDate) AS Month, 
            SUM(o.Invoice) AS Revenue
        FROM 
            OrderData o
        JOIN 
            UserLevelData u ON o.Userid = u.Userid
        GROUP BY 
            u.Industry, 
            Month
    )

    SELECT 
        Industry, 
        ROUND(AVG(Revenue), 2) AS "AverageMonthlyRevenue (USD)"
    FROM 
        monthly_revenues
    GROUP BY 
        Industry;
    """
    # Write resultset returned by the query to the dataframe
    industry_revenue_df = execute_sql_query(query, engine)
    
    # Display the Output Table
    with st.expander("View Output Table ..."):
        filtered_df = dataframe_explorer(industry_revenue_df, case=False)
        st.dataframe(filtered_df, use_container_width=True)
     
    # Display Chart
    fig = px.bar(industry_revenue_df, x='Industry', y='AverageMonthlyRevenue (USD)')
    fig.update_layout(height=600)
    st.plotly_chart(fig,use_container_width=True)
    
    
    
    
# Section 2

def top_performers_by_industry():
    st.title('Top Performers by Industry')

    # Add a selectbox to display no. of top performers 
    top_n = st.selectbox(
        'Select number of top performers to display:',
        [1, 2, 3, 4, 5]
    )

    
    query = f"""
    WITH total_revenue AS (
        SELECT 
            u.Industry,
            o.Userid,
            ROUND(SUM(o.Invoice), 2) as TotalRevenue,
            ROW_NUMBER() OVER (PARTITION BY u.Industry ORDER BY SUM(o.Invoice) DESC) as rn
        FROM 
            OrderData o
        INNER JOIN 
            UserLevelData u ON o.Userid = u.Userid
        GROUP BY 
            u.Industry, o.Userid
    )

    SELECT 
        Industry, 
        Userid, 
        TotalRevenue as "TotalRevenue (USD)"
    FROM 
        total_revenue
    WHERE 
        rn <= {top_n}
    ORDER BY 
        Industry ASC, TotalRevenue DESC;
    """
    
    # Write resultset returned by the query to the dataframe
    top_performers_df = execute_sql_query(query, engine)

    # Convert 'Userid' to string for better display
    top_performers_df['Userid'] = top_performers_df['Userid'].astype(str)

    
    # Display the Output Table
    with st.expander("View Output Table ..."):
        filtered_df = dataframe_explorer(top_performers_df, case=False)
        st.dataframe(filtered_df, use_container_width=True)
        
        
    # Create the bar chart
    fig = px.bar(
        top_performers_df, 
        x='Industry', 
        y='TotalRevenue (USD)', 
        color='Userid', 
        title=f'Top {top_n} Users by Industry Based on Overall Revenue',
        labels={'TotalRevenue (USD)': 'Total Revenue (USD)', 'Industry': 'Industry', 'Userid': 'User ID'},
        height=600,
        barmode='group'
    )

    # Rotate x-axis labels
    fig.update_layout(
        xaxis_tickangle=-45,
        autosize=True,
        margin=dict(l=50, r=50, b=100, t=100, pad=4),
        height=600,
    )

    # Display the chart
    st.plotly_chart(fig,use_container_width=True)
    
    
    

# Section 3

def MoM_user_revenue_order_counts():
    st.title('Monthly User Revenue and Order Counts')
    

    query = """
    SELECT 
        Userid AS "User ID",
        SUM(CASE WHEN MONTH(PurchaseDate) = 9 AND YEAR(PurchaseDate) = 2020 THEN ROUND(Invoice,2) ELSE 0 END) AS "Revenue USD (Previous -1 Month)",
        COUNT(CASE WHEN MONTH(PurchaseDate) = 9 AND YEAR(PurchaseDate) = 2020 THEN 1 END) AS "Order Count (Previous -1 Month)",
        SUM(CASE WHEN MONTH(PurchaseDate) = 10 AND YEAR(PurchaseDate) = 2020 THEN ROUND(Invoice,2) ELSE 0 END) AS "Revenue USD (Previous Month)",
        COUNT(CASE WHEN MONTH(PurchaseDate) = 10 AND YEAR(PurchaseDate) = 2020 THEN 1 END) AS "Order Count (Previous Month)",
        SUM(CASE WHEN MONTH(PurchaseDate) = 11 AND YEAR(PurchaseDate) = 2020 THEN ROUND(Invoice,2) ELSE 0 END) AS "Revenue USD (Current Month)",
        COUNT(CASE WHEN MONTH(PurchaseDate) = 11 AND YEAR(PurchaseDate) = 2020 THEN 1 END) AS "Order Count (Current Month)"
    FROM 
        OrderData
    GROUP BY 
        Userid;

    """
    
    # Write resultset returned by the query to the dataframe
    df = execute_sql_query(query, engine)
    
    # Display the Output Table
    with st.expander("View Output Table ..."):
        filtered_df = dataframe_explorer(df, case=False)
        st.dataframe(filtered_df, use_container_width=True)
        
        
        
    # Reshape the DataFrame to "long" format for easier plotting
    df_melted = df.melt(id_vars='User ID', var_name='Month', value_name='Value')

    # Separate revenue and order count data
    df_revenue = df_melted[df_melted['Month'].str.contains('Revenue')]
    df_orders = df_melted[df_melted['Month'].str.contains('Order Count')]

    # Convert 'Month' column to more readable format
    df_revenue['Month'] = df_revenue['Month'].map({'Revenue USD (Current Month)': 'November 2020',
                                                    'Revenue USD (Previous Month)': 'October 2020',
                                                    'Revenue USD (Previous -1 Month)': 'September 2020'})

    df_orders['Month'] = df_orders['Month'].map({'Order Count (Current Month)': 'November 2020',
                                                'Order Count (Previous Month)': 'October 2020',
                                                'Order Count (Previous -1 Month)': 'September 2020'})

    # Get unique User IDs for the selectbox option
    user_ids = df_revenue['User ID'].unique()

    # Use selectbox to let the user select a User ID
    selected_user = st.selectbox('Select User ID', options=user_ids, key='unique_key')

    df_revenue_selected = df_revenue[df_revenue['User ID'] == selected_user]
    df_orders_selected = df_orders[df_orders['User ID'] == selected_user]

    # Create a subplot with 1 row and 2 columns
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Revenue", "Order Count"))

    # Add traces
    fig.add_trace(go.Scatter(x=df_revenue_selected['Month'], y=df_revenue_selected['Value'],mode='lines+markers', name='Revenue', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_orders_selected['Month'], y=df_orders_selected['Value'], mode='lines+markers', name='Order Count', line=dict(color='red')), row=1, col=2)

    # Update xaxis properties
    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=1, col=2)

    # Update yaxis properties
    fig.update_yaxes(title_text="Revenue", row=1, col=1)
    fig.update_yaxes(title_text="Order Count", row=1, col=2)

    # Update title and size
    fig.update_layout(title_text=f'User ID: {selected_user}', autosize=False, width=1200, height=600, margin=dict(l=50, r=50, b=100, t=100, pad=4))

    # Display the Chart
    st.plotly_chart(fig,use_container_width=True)

    
    





# Create a dictionary that maps the page name to the function that should be called
pages = {
    "Industry Earnings": industry_avg_monthly_revenue,
    "Top Performers": top_performers_by_industry,
    "Sales Trends": MoM_user_revenue_order_counts
}


# Use the option_menu to select the page you want to display
selected_page = option_menu(None, list(pages.keys()), menu_icon="cast", default_index=0, orientation="horizontal")

# Call the function to display the selected page
pages[selected_page]()
