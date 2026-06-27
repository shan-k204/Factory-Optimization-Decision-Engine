import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Factory Optimization",
    page_icon="🏭",
    layout="wide"
)

df = pd.read_csv(
    "Data/Processed_nassau_candy_data.csv"
)

df["Order Date"] = pd.to_datetime(df["Order Date"])

st.sidebar.markdown("<div style='height:75px'></div>", unsafe_allow_html=True)

with st.sidebar.container():

    st.sidebar.markdown("""
    <div style="
    background:rgba(168,85,247,0.12);
    padding:15px;
    border-radius:12px;
    border:1px solid rgba(168,85,247,0.25);
    ">
    <h3>🔍 Filters</h3>
    <p>Select factory and region to explore performance metrics.</p>
    </div>
    <br>
    """, unsafe_allow_html=True)


selected_factory = st.sidebar.selectbox(
    "🏭 Select Factory",
    ["All"] + sorted(df["Factory"].unique().tolist())
)

selected_region = st.sidebar.selectbox(
    "🌎 Select Region",
    ["All"] + sorted(df["Region"].unique().tolist())
)

start_date = st.sidebar.date_input(
    "📅 Start Date",
    value=df["Order Date"].min().date(),
    min_value=df["Order Date"].min().date(),
    max_value=df["Order Date"].max().date()
)

end_date = st.sidebar.date_input(
    "📅 End Date",
    value=df["Order Date"].max().date(),
    min_value=df["Order Date"].min().date(),
    max_value=df["Order Date"].max().date()
)

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

if end_date < start_date:
    st.sidebar.warning(
        "End Date cannot be before Start Date"
    )
    end_date = start_date

filtered_df = df.copy()

if selected_factory != "All":
    filtered_df = filtered_df[
        filtered_df["Factory"] == selected_factory
    ]

if selected_region != "All":
    filtered_df = filtered_df[
        filtered_df["Region"] == selected_region
    ]
    
filtered_df = filtered_df[
    (filtered_df["Order Date"] >= pd.to_datetime(start_date))
    &
    (filtered_df["Order Date"] <= pd.to_datetime(end_date))
]

if filtered_df.empty:
    
    filtered_df = pd.DataFrame(
        columns=df.columns
    )

    st.info(
        "No records found for the selected date range."
    )

benchmark_df = df.copy()

if selected_region != "All":
    benchmark_df = benchmark_df[
        benchmark_df["Region"] == selected_region
    ]

benchmark_df = benchmark_df[
    (benchmark_df["Order Date"] >= start_date)
    &
    (benchmark_df["Order Date"] <= end_date)
]

ranking_summary = (
    benchmark_df.groupby("Factory")
    .agg({
        "Lead_Time":"mean",
        "Gross Profit":"sum",
        "Sales":"sum"
    })
    .round(2)
)

if not ranking_summary.empty:

    ranking_summary["Profit_Score"] = (
        ranking_summary["Gross Profit"]
        / ranking_summary["Gross Profit"].max()
    ) * 100

    lead_min = ranking_summary["Lead_Time"].min()
    lead_max = ranking_summary["Lead_Time"].max()

    if lead_max == lead_min:

        ranking_summary["LeadTime_Score"] = 100

    else:

        ranking_summary["LeadTime_Score"] = (
            (lead_max - ranking_summary["Lead_Time"])
            /
            (lead_max - lead_min)
        ) * 100

    ranking_summary["Optimization_Score"] = (
        0.6 * ranking_summary["Profit_Score"]
        +
        0.4 * ranking_summary["LeadTime_Score"]
    )

else:

    st.warning(
        "⚠️ No optimization recommendation available for selected filters."
    )

    optimization_df = pd.DataFrame()
    
factory_profit = (
    filtered_df.groupby("Factory")["Gross Profit"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
    .round(2)
)

leadtime_df = (
    benchmark_df.groupby("Factory")["Lead_Time"]
    .mean()
    .sort_values()
    .reset_index()
    .round(2)
)

avg_lead = (
    round(filtered_df["Lead_Time"].mean(), 2)
    if not filtered_df.empty
    else 0
)

st.markdown("""
<div style="
padding:25px;
border-radius:15px;
background: linear-gradient(90deg,#3b82f6,#9333ea);
text-align:center;
margin-bottom:25px;
">
<h1 style="color:white;">
🏭 Nassau Candy Factory Decision Engine 🍬
</h1>

<p style="color:white;">
Optimize factory allocation, predict profitability,
and simulate operational scenarios in real-time.
</p>

</div>
""", unsafe_allow_html=True)

st.caption(
    "Identify the most efficient factory based on profitability and lead-time performance using a weighted optimization scoring model."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📈 Analysis",
    "🎮 Simulation",
    "🗂️ Data Explorer"
])

optimization_df = (
    ranking_summary
    .sort_values(
        by="Optimization_Score",
        ascending=False
    )
    .reset_index()
    .round(2)
)

# Build the rank dictionary first
factory_rank = {}

for i, name in enumerate(optimization_df["Factory"]):

    if i == 0:
        factory_rank[name] = "🥇"
    elif i == 1:
        factory_rank[name] = "🥈"
    elif i == 2:
        factory_rank[name] = "🥉"
    else:
        factory_rank[name] = "🏅"

    # Create the Rank column
    optimization_df["Rank"] = (
        optimization_df["Factory"]
        .map(factory_rank)
    )

    # NOW reorder the columns
    optimization_df = optimization_df[
        [
            "Rank",
            "Factory",
            "Lead_Time",
            "Gross Profit",
            "Sales",
            "Profit_Score",
            "LeadTime_Score",
            "Optimization_Score"
        ]
    ]

    best_factory = optimization_df.iloc[0]
    
def show_filter_status():
    
    with st.expander("🔍 Current Filters & Data Status", expanded=False):

        st.write(f"🏭 Factory: {selected_factory}")
        st.write(f"🌎 Region: {selected_region}")
        st.write(f"📅 Date: {start_date.date()} → {end_date.date()}")
        st.write(f"📊 Records: {len(benchmark_df):,}")

        if benchmark_df.empty:
            st.warning("No matching records found.")
        else:
            st.success("Data loaded successfully.")

with tab1:
    
  show_filter_status()

  st.markdown("## 📊 Key Performance Indicators")
  
  best_profit = ranking_summary["Gross Profit"].idxmax()
  fastest = ranking_summary["Lead_Time"].idxmin()
  slowest = ranking_summary["Lead_Time"].idxmax()
  lowest_profit = ranking_summary["Gross Profit"].idxmin()

  col1, col2, col3, col4 = st.columns(4)

  with col1:
    st.markdown(f"""
    <div class="metric-card">
        💰 Total Sales
        <h4>${filtered_df['Sales'].sum():,.0f}</h4>
    </div>
    """, unsafe_allow_html=True)

  with col2:
    st.markdown(f"""
    <div class="metric-card">
        📈 Total Profit
        <h4>${filtered_df['Gross Profit'].sum():,.0f}</h4>
    </div>
    """, unsafe_allow_html=True)

  with col3:
    st.markdown(f"""
    <div class="metric-card">
        🚚 Avg Lead Time
        <h4>{avg_lead} Days</h4>
    </div>
    """, unsafe_allow_html=True)

  with col4:
    st.markdown(f"""
    <div class="metric-card">
        🏭 Factories
        <h4>{filtered_df["Factory"].nunique()}</h4>
    </div>
    """, unsafe_allow_html=True)
      
  st.markdown("---")    
  
  st.markdown("## 📋 Factory Performance Summary")
  
  st.info(
        f"🏆 Best Performing Factory: {best_factory['Factory']} | Optimization Score: {best_factory['Optimization_Score']:.2f}"
    )

  st.dataframe(
      optimization_df,
      hide_index=True,
      use_container_width=True
  )
  
  with st.expander("📌 Key Business Recommendations"):

    st.markdown("""
    ### Recommendations

    ✅ Allocate premium orders to Lot's O' Nuts because it generates the highest profit.

    🚚 Secret Factory has the fastest delivery performance and should be preferred for urgent shipments.

    ⚠️ Wicked Choccy's is profitable but has slower lead times. Consider operational improvements before increasing workload.

    📦 Sugar Shack contributes very little profit and should be reviewed for cost optimization.
    """)

with tab2:
    
    show_filter_status()

    st.markdown("## 📈 Factory Analysis")
    
    st.markdown("""
    <style>
    .metric-card{
        background: rgba(168,85,247,0.15);
        padding:15px;
        border-radius:12px;
        border:1px solid rgba(168,85,247,0.3);
    }
    </style>
    """, unsafe_allow_html=True)
   
    col1, col2, col3 = st.columns(3)
   
    if (
        selected_factory != "All"
        and
        selected_factory in ranking_summary.index
        and
        "Optimization_Score" in ranking_summary.columns
    ):

        score = round(
            ranking_summary.loc[
                selected_factory,
                "Optimization_Score"
            ],
            2
        )

    elif (
        not ranking_summary.empty
        and
        "Optimization_Score" in ranking_summary.columns
    ):

        score = round(
            ranking_summary[
                "Optimization_Score"
            ].mean(),
            2
        )

    else:

        score = 0
        
    date_filtered_df = df.copy()

    if selected_region != "All":
        date_filtered_df = date_filtered_df[
            date_filtered_df["Region"] == selected_region
        ]

    date_filtered_df = date_filtered_df[
        (date_filtered_df["Order Date"] >= start_date)
        &
        (date_filtered_df["Order Date"] <= end_date)
    ]

    factory_profit = (
        date_filtered_df
        .groupby("Factory")["Gross Profit"]
        .sum()
    )
    
    total_profit = factory_profit.sum()

    if (
        selected_factory != "All"
        and
        selected_factory in factory_profit.index
        and
        total_profit > 0
    ):

        profit_share = round(
            (
                factory_profit[selected_factory]
                /
                total_profit
            ) * 100,
            2
        )

    elif total_profit > 0:

        profit_share = 100

    else:

        profit_share = 0

    profit_share_display = f"{profit_share}%"

    with col1:

        selected_factory_display = (
            selected_factory
            if selected_factory != "All"
            else "All Factories"
        )

        st.markdown(f"""
        <div class="metric-card">
            🏭 Selected Factory
            <h4>{selected_factory_display}</h4>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            🎯 Performance Score
            <h4>{score}%</h4>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            💰 Profit Share
            <h4>{profit_share_display}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if (
        selected_factory != "All"
        and
        selected_factory in ranking_summary.index
    ):

        current_score = ranking_summary.loc[
            selected_factory,
            "Optimization_Score"
        ]

    elif not ranking_summary.empty:

        current_score = (
            ranking_summary["Optimization_Score"]
            .mean()
        )

    else:

        current_score = 0
    
    chart_col1, chart_col2 = st.columns([1,1])
    
    fig_gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=current_score,
        number={"suffix":"%"},
        delta={
            "reference":0,
            "relative":False
        },
        
        title={
            "text":"Factory Performance Score",
            "font":{"size":29},
        },
        
        gauge={
            "axis":{"range":[0,100]},
            "bar":{"thickness":0.9, "color":"#A855F7"},

            "steps":[
                {"range":[0,40], "color":"#7F1D1D"},
                {"range":[40,70],"color":"#92400E"},
                {"range":[70,100],"color":"#06d6a0"}
            ]
        }
    )
 )

    fig_gauge.update_layout(
    height=350,
    margin=dict(t=90, b=50, l=50, r=50)                        
    )
   
    with chart_col1:
        st.plotly_chart(
            fig_gauge,
            use_container_width=False
        )
        
    pie_df = (
        date_filtered_df
        .groupby("Factory")["Gross Profit"]
        .sum()
        .reset_index()
        .sort_values(
            by="Gross Profit",
            ascending=False
        )
    )
    
    fig_pie = px.pie(
    pie_df,
    names="Factory",
    values="Gross Profit",
    hole=0.65,
    title="Profit Share by Factory",
    color_discrete_sequence=[
        "#EC4899",  # Pink
        "#A855F7",  # Purple
        "#6366F1",  # Indigo
        "#F472B6",  # Light Pink
        "#C084FC"   # Lavender
    ]
    )

    with chart_col2:

        fig_pie.update_layout(
            height=390,
            width=600
        )

        st.plotly_chart(
            fig_pie,
            use_container_width=True
        )
    
    if current_score >= 70:
       
     st.markdown(
    """
        <div style="
            text-align:center;
            font-size:14px;
            font-weight:bold;
            color:#22C55E;
            background-color: rgba(59, 130, 246, 0.15);
            padding: 8px 12px;
            border-radius: 8px;
            margin-top:-5px;
            border: 1px solid rgba(59, 130, 246, 0.3);
        ">
        High Performing Factory
        </div>
        """,
        unsafe_allow_html=True
    )
    
    elif current_score >= 40:
        st.markdown(
        """
        <div style="
            text-align:center;
            font-size:14px;
            font-weight:bold;
            color:#60A5FA;
            background-color: rgba(59, 130, 246, 0.15);
            padding: 8px 12px;
            border-radius: 8px;
            margin-top:-5px;
            border: 1px solid rgba(59, 130, 246, 0.3);
        ">
        Moderate Performance
        </div>
        """,
        unsafe_allow_html=True
    )
   
    else:
        st.markdown(
        """
        <div style="
            text-align:center;
            font-size:14px;
            font-weight:bold;
            color:#F97316;
            background-color: rgba(59, 130, 246, 0.15);
            padding: 8px 12px;
            border-radius: 8px;
            margin-top:-5px;
            border: 1px solid rgba(59, 130, 246, 0.3);
        ">
        Improvement Opportunity
        </div>
        """,
        unsafe_allow_html=True
    )
    
    revenue_profit_df = (
    benchmark_df.groupby("Factory")
    .agg({
        "Sales": "sum",
        "Gross Profit": "sum"
    })
    .reset_index()
    )
    
    fig_revenue = px.bar(
    revenue_profit_df,
    x="Factory",
    y=["Sales", "Gross Profit"],
    barmode="group",
    title="Revenue vs Profit by Factory",
    color_discrete_sequence=[
        "#EC4899",  # Sales
        "#A855F7"   # Profit
    ]
    )
    
    fig_revenue.update_traces(
    hovertemplate=
    "<b>%{x}</b><br>" +
    "Metric: %{fullData.name}<br>" +
    "Value: %{y:,.0f}<extra></extra>"
    )
    
    fig_revenue.update_layout(
        legend_title_text="",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f"
    )

    st.plotly_chart(
       fig_revenue,
       use_container_width=True
    )

    fig_leadtime = px.bar(
        leadtime_df,
        text="Lead_Time",
        x="Factory",
        y="Lead_Time",
        title="Average Lead Time by Factory",
        color="Lead_Time",
        color_continuous_scale="reds"
    )
    
    fig_leadtime.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    st.plotly_chart(
        fig_leadtime,
        use_container_width=True
    )

with tab3:

   st.markdown("## 🎮 Scenario Simulator")
   
   st.caption(
    "Simulate different factory, shipping mode, region, and unit combinations to estimate profitability and operational impact."
 )

   def simulate_scenario(
       factory,
       ship_mode,
       region,
       units
   ):

    filtered = df[
        (df["Factory"] == factory)
        &
        (df["Ship Mode"] == ship_mode)
        &
        (df["Region"] == region)
    ]

    if filtered.empty:
           return None

    avg_profit = filtered["Gross Profit"].mean()
    avg_leadtime = filtered["Lead_Time"].mean()

    expected_profit = avg_profit * units

    if avg_leadtime <= 4:
        recommendation = "Fast Delivery"

    elif avg_leadtime <= 7:
        recommendation = "Balanced Option"

    else:
        recommendation = "Slow but Economical"

    return {
        "Expected Profit": round(expected_profit, 2),
        "Expected Lead Time": round(avg_leadtime, 2),
        "Recommendation": recommendation
    }

   factory = st.selectbox(
       "Factory",
       sorted(df["Factory"].unique())
   )

   ship_mode = st.selectbox(
       "Ship Mode",
       sorted(df["Ship Mode"].unique())
   )

   region = st.selectbox(
       "Region",
       sorted(df["Region"].unique())
   )

   units = st.number_input(
       "Units",
       min_value=1,
       value=50
   )
   
   rank_icon = factory_rank.get(
        factory,
        "🏭"
    )

   st.success(
        f"{rank_icon} Factory Ranking: {factory}"
    )

   run_simulation = st.button(
       "🚀 Run Simulation"
   )

   if run_simulation:

    result = simulate_scenario(
        factory,
        ship_mode,
        region,
        units
    )

    if result is None:
        st.warning(
            "⚠️ No historical data found for this scenario."
        )

    else:
        
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                💰 Expected Profit
                <h4>${result['Expected Profit']:,.2f}</h4>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                🚚 Lead Time
                <h4>{result['Expected Lead Time']} Days</h4>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                🎯 Recommendation
                <h4>{result["Recommendation"]}</h4>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        unit_levels = [10, 25, 50, 100, 200]

        projection_df = pd.DataFrame({
            "Units": unit_levels,
            "Projected Profit": [
                (result["Expected Profit"] / units) * u
                for u in unit_levels
        ]
        })
        
        fig = px.line(
        projection_df,
        x="Units",
        y="Projected Profit",
        title="Profit Projection by Units",
        markers=True
    )

        fig.update_traces(
            line=dict(width=4),
            marker=dict(size=10)
        )

        fig.update_layout(
            xaxis_title="Units",
            yaxis_title="Projected Profit ($)"
        )
        
        scatter_df = (
        df.groupby("Factory")
        .agg({
            "Gross Profit": "mean",
            "Lead_Time": "mean"
        })
        .reset_index()
        .round(2)
    )
        
        fig_scatter = px.scatter(
            scatter_df,
            x="Lead_Time",
            y="Gross Profit",
            color="Factory",
            size="Gross Profit",
            hover_name="Factory",
            title="Factory Tradeoff"
    )
        fig_scatter.update_traces(
            marker=dict(
                sizemin=12,
                opacity=0.85
            )
    )
        
        col_chart1, col_chart2 = st.columns([1, 1])

        with col_chart1:

            st.plotly_chart(
                fig,
                use_container_width=True
        )

        with col_chart2:

            fig_scatter.update_layout(
                xaxis_title="Average Lead Time (Days)",
                yaxis_title="Average Gross Profit",
                showlegend=False,
                height=450
            )

            st.plotly_chart(
            fig_scatter,
            use_container_width=True
            )
        
with tab4:

    st.markdown("## 🗂️ Data Explorer")

    st.caption(
        "Explore the filtered dataset used throughout the dashboard."
    )

    rows = st.selectbox(
        "Rows",
        [25,50,100,250]
    )

    st.dataframe(
        filtered_df.head(rows),
        use_container_width=True
    )

    st.download_button(
        "📥 Download Filtered Data",
        filtered_df.to_csv(index=False),
        "filtered_factory_data.csv",
        "text/csv"
    )