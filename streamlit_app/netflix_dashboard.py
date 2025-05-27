import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import joblib # To save/load models and encoders

# Set page config with Netflix theme
st.set_page_config(
    page_title="Netflix Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Netflix-style CSS
st.markdown("""
    <style>
    /* Import Netflix font */
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue:wght@400&family=Roboto:wght@300;400;500;700&display=swap');

    /* Main background */
    .main {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
        color: #ffffff;
        font-family: 'Roboto', sans-serif;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #E50914 0%, #B20710 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(229, 9, 20, 0.3);
    }

    .main-title {
        font-family: 'Bebas Neue', cursive;
        font-size: 3.5rem;
        color: white;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    .main-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #f0f0f0;
        margin-top: 0.5rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
    }

    /* Metric cards */
    .metric-container {
        background: linear-gradient(135deg, #2a2a2a 0%, #1f1f1f 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #333;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin: 0.5rem 0;
        transition: transform 0.3s ease;
    }

    .metric-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(229, 9, 20, 0.2);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #E50914;
        margin: 0;
    }

    .metric-label {
        font-size: 1rem;
        color: #cccccc;
        margin: 0;
    }

    /* Custom styling for various elements */
    h1, h2, h3 {
        color: #E50914;
        font-family: 'Bebas Neue', cursive;
    }

    /* Filter section */
    .filter-header {
        background: linear-gradient(90deg, #E50914 0%, #B20710 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #333333 0%, #444444 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #E50914;
        margin: 1rem 0;
    }

    .stSelectbox > div > div {
        background-color: #2a2a2a;
        color: white;
    }

    .stMultiSelect > div > div {
        background-color: #2a2a2a;
        color: white;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Custom header
st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🎬 NETFLIX ANALYTICS</h1>
        <p class="main-subtitle">Discover trends, patterns, and insights in Netflix's content library</p>
    </div>
    """, unsafe_allow_html=True)

# Load and clean data function
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('netflix_titles.csv')
        # Clean and prepare data
        df = df.dropna(subset=['type', 'release_year'])
        df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
        df = df.dropna(subset=['release_year'])
        df['release_year'] = df['release_year'].astype(int)

        # Clean country data
        df['country'] = df['country'].fillna('Unknown')
        df['first_country'] = df['country'].str.split(',').str[0].str.strip()

        # Process genres
        df['listed_in'] = df['listed_in'].fillna('Unknown')

        # Drop rows with missing 'rating' for prediction model
        df = df.dropna(subset=['rating'])

        return df
    except FileNotFoundError:
        st.error("Netflix dataset not found. Please ensure 'netflix_titles.csv' is in the same directory.")
        return pd.DataFrame()

# Load data
df = load_data()

if df.empty:
    st.stop()

# --- Machine Learning Model Training/Loading ---
# This section should ideally be run once to train and save the model/encoders.
# For a deployed app, you'd load pre-trained assets.

@st.cache_resource # Use st.cache_resource for models/heavy objects
def train_and_load_model(dataframe):
    # Prepare data for the model
    model_df = dataframe.copy()
    model_df = model_df.dropna(subset=['country', 'release_year', 'rating', 'listed_in', 'type'])

    # Initialize LabelEncoders
    le_country = LabelEncoder()
    le_rating = LabelEncoder()
    le_genre = LabelEncoder()
    le_type = LabelEncoder()

    # Fit and transform categorical features
    model_df['country_encoded'] = le_country.fit_transform(model_df['country'])
    model_df['rating_encoded'] = le_rating.fit_transform(model_df['rating'])
    model_df['genre_encoded'] = le_genre.fit_transform(model_df['listed_in'])
    model_df['type_encoded'] = le_type.fit_transform(model_df['type'])

    # Define features (X) and target (y)
    X = model_df[['country_encoded', 'release_year', 'rating_encoded', 'genre_encoded']]
    y = model_df['type_encoded']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a simple classifier (e.g., Decision Tree)
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)

    return model, le_country, le_rating, le_genre, le_type

# Load or train the model and encoders
try:
    # Attempt to load pre-trained model and encoders
    model = joblib.load('netflix_type_predictor_model.joblib')
    le_country = joblib.load('le_country.joblib')
    le_rating = joblib.load('le_rating.joblib')
    le_genre = joblib.load('le_genre.joblib')
    le_type = joblib.load('le_type.joblib')
except FileNotFoundError:
    st.info("Training a new prediction model. This might take a moment...")
    model, le_country, le_rating, le_genre, le_type = train_and_load_model(df)
    # Save the trained model and encoders for future use
    joblib.dump(model, 'netflix_type_predictor_model.joblib')
    joblib.dump(le_country, 'le_country.joblib')
    joblib.dump(le_rating, 'le_rating.joblib')
    joblib.dump(le_genre, 'le_genre.joblib')
    joblib.dump(le_type, 'le_type.joblib')


# Enhanced Sidebar with Netflix styling
st.sidebar.markdown("""
    <div class="filter-header">
        <h2 style="margin: 0; color: white; text-align: center;">🎯 FILTERS</h2>
    </div>
    """, unsafe_allow_html=True)

# Content type filter
content_types = st.sidebar.multiselect(
    "🎭 Content Type",
    options=df['type'].unique(),
    default=df['type'].unique(),
    help="Select the type of content to analyze"
)

# Country filter (top 20 countries)
top_countries = df['first_country'].value_counts().head(20).index.tolist()
selected_countries = st.sidebar.multiselect(
    "🌍 Countries",
    options=top_countries,
    default=top_countries[:5],
    help="Select countries to analyze"
)

# Year range slider
year_range = st.sidebar.slider(
    "📅 Release Year Range",
    min_value=int(df['release_year'].min()),
    max_value=int(df['release_year'].max()),
    value=(2015, int(df['release_year'].max())),
    help="Select the range of release years"
)

# Rating filter
available_ratings = df['rating'].dropna().unique()
selected_ratings = st.sidebar.multiselect(
    "⭐ Content Ratings",
    options=available_ratings,
    default=available_ratings,
    help="Select content ratings to include"
)

# Apply filters
filtered_df = df[
    (df['type'].isin(content_types)) &
    (df['first_country'].isin(selected_countries)) &
    (df['release_year'].between(year_range[0], year_range[1])) &
    (df['rating'].isin(selected_ratings))
]

# Main metrics with enhanced styling
st.markdown("## 📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

total_titles = len(filtered_df)
total_movies = len(filtered_df[filtered_df['type'] == 'Movie'])
total_shows = len(filtered_df[filtered_df['type'] == 'TV Show'])
avg_year = int(filtered_df['release_year'].mean()) if not filtered_df.empty else 0

with col1:
    st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{total_titles:,}</p>
            <p class="metric-label">Total Titles</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{total_movies:,}</p>
            <p class="metric-label">Movies</p>
        </div>
        """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{total_shows:,}</p>
            <p class="metric-label">TV Shows</p>
        </div>
        """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{avg_year}</p>
            <p class="metric-label">Avg Release Year</p>
        </div>
        """, unsafe_allow_html=True)

# Check if we have data to display
if filtered_df.empty:
    st.warning("No data matches your current filters. Please adjust your selection.")
    st.stop()

# Interactive Charts Section
st.markdown("## 📈 Interactive Analytics")

# Create tabs for different chart categories
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🌍 Geographic",
    "📅 Temporal",
    "🎭 Content Analysis",
    "🧠 Type Predictor"
])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        # Content Type Distribution - Donut Chart
        type_counts = filtered_df['type'].value_counts()
        fig_donut = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title="Content Type Distribution",
            hole=0.4,
            color_discrete_sequence=['#E50914', '#B20710']
        )
        fig_donut.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        # Top Ratings Distribution
        rating_counts = filtered_df['rating'].value_counts().head(8)
        fig_rating = px.bar(
            x=rating_counts.values,
            y=rating_counts.index,
            orientation='h',
            title="Content by Rating",
            color=rating_counts.values,
            color_continuous_scale='Reds'
        )
        fig_rating.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20,
            showlegend=False
        )
        st.plotly_chart(fig_rating, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    with col1:
        # Top Countries
        country_counts = filtered_df['first_country'].value_counts().head(15)
        fig_countries = px.bar(
            x=country_counts.values,
            y=country_counts.index,
            orientation='h',
            title="Top 15 Countries by Content Volume",
            color=country_counts.values,
            color_continuous_scale='Reds'
        )
        fig_countries.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20,
            height=500
        )
        st.plotly_chart(fig_countries, use_container_width=True)

    with col2:
        # Content Type by Country (Top 10 countries)
        top_countries_content = filtered_df[filtered_df['first_country'].isin(country_counts.head(10).index)]
        country_type_df = top_countries_content.groupby(['first_country', 'type']).size().reset_index(name='count')

        fig_country_type = px.bar(
            country_type_df,
            x='first_country',
            y='count',
            color='type',
            title="Movies vs TV Shows by Country",
            color_discrete_map={'Movie': '#E50914', 'TV Show': '#B20710'}
        )
        fig_country_type.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_country_type, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)

    with col1:
        # Content Release Timeline
        yearly_counts = filtered_df.groupby(['release_year', 'type']).size().reset_index(name='count')
        fig_timeline = px.line(
            yearly_counts,
            x='release_year',
            y='count',
            color='type',
            title="Content Release Timeline",
            markers=True,
            color_discrete_map={'Movie': '#E50914', 'TV Show': '#B20710'}
        )
        fig_timeline.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col2:
        # Monthly Release Pattern (if date_added is available)
        if 'date_added' in filtered_df.columns and not filtered_df['date_added'].isna().all():
            filtered_df['date_added'] = pd.to_datetime(filtered_df['date_added'], errors='coerce')
            filtered_df['month_added'] = filtered_df['date_added'].dt.month_name()
            month_counts = filtered_df['month_added'].value_counts()

            fig_monthly = px.bar(
                x=month_counts.index,
                y=month_counts.values,
                title="Content Added by Month",
                color=month_counts.values,
                color_continuous_scale='Reds'
            )
            fig_monthly.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_size=20,
                showlegend=False
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            # Decade distribution as alternative
            filtered_df['decade'] = (filtered_df['release_year'] // 10) * 10
            decade_counts = filtered_df['decade'].value_counts().sort_index()

            fig_decade = px.bar(
                x=decade_counts.index.astype(str) + 's',
                y=decade_counts.values,
                title="Content by Decade",
                color=decade_counts.values,
                color_continuous_scale='Reds'
            )
            fig_decade.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_size=20,
                showlegend=False
            )
            st.plotly_chart(fig_decade, use_container_width=True)

with tab4:
    col1, col2 = st.columns(2)

    with col1:
        # Top Genres
        genres = filtered_df['listed_in'].str.split(', ').explode()
        top_genres = genres.value_counts().head(15)

        fig_genres = px.treemap(
            names=top_genres.index,
            values=top_genres.values,
            title="Top Genres (Treemap)",
            color=top_genres.values,
            color_continuous_scale='Reds'
        )
        fig_genres.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20
        )
        st.plotly_chart(fig_genres, use_container_width=True)

    with col2:
        # Duration Analysis (if available)
        if 'duration' in filtered_df.columns:
            # Process duration data
            movies_duration = filtered_df[filtered_df['type'] == 'Movie']['duration'].str.extract('(\d+)').astype(float)
            shows_duration = filtered_df[filtered_df['type'] == 'TV Show']['duration'].str.extract('(\d+)').astype(float)

            fig_duration = go.Figure()
            if not movies_duration.empty:
                fig_duration.add_trace(go.Histogram(x=movies_duration[0], name='Movies', opacity=0.7, marker_color='#E50914'))
            if not shows_duration.empty:
                fig_duration.add_trace(go.Histogram(x=shows_duration[0], name='TV Shows', opacity=0.7, marker_color='#B20710'))

            fig_duration.update_layout(
                title="Duration Distribution",
                xaxis_title="Duration",
                yaxis_title="Count",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_size=20
            )
            st.plotly_chart(fig_duration, use_container_width=True)
        else:
            # Alternative: Rating vs Release Year scatter
            fig_scatter = px.scatter(
                filtered_df.sample(min(1000, len(filtered_df))),
                x='release_year',
                y='rating',
                color='type',
                title="Content Rating vs Release Year",
                color_discrete_map={'Movie': '#E50914', 'TV Show': '#B20710'},
                opacity=0.6
            )
            fig_scatter.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_size=20
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

# 🧠 NEW: Title Type Predictor Tab
with tab5:
    st.markdown("## 🧠 Netflix Title Type Predictor")
    st.markdown("Enter a Netflix title and the model will predict whether it's a **Movie** or a **TV Show**.")

    title_input = st.text_input("🎬 Enter Netflix Title")

    if st.button("Predict Type"):
        if title_input.strip() == "":
            st.warning("Please enter a title first.")
        else:
            try:
                matched_row = df[df['title'].str.lower() == title_input.lower()]
                if matched_row.empty:
                    st.error("❌ Title not found in dataset. Try a known Netflix title.")
                else:
                    # Retrieve original values for encoding
                    original_genre = matched_row.iloc[0]['listed_in']
                    country = matched_row.iloc[0]['country']
                    release_year = matched_row.iloc[0]['release_year']
                    rating = matched_row.iloc[0]['rating']

                    # Ensure the values can be transformed by the encoders
                    # Handle cases where a value might not have been seen during training
                    try:
                        country_encoded = le_country.transform([country])[0]
                    except ValueError:
                        country_encoded = -1 # Or handle by predicting a default/most common
                        st.warning(f"Country '{country}' not seen in training data. Using a default encoding.")
                    try:
                        rating_encoded = le_rating.transform([rating])[0]
                    except ValueError:
                        rating_encoded = -1
                        st.warning(f"Rating '{rating}' not seen in training data. Using a default encoding.")
                    try:
                        genre_encoded = le_genre.transform([original_genre])[0]
                    except ValueError:
                        genre_encoded = -1
                        st.warning(f"Genre '{original_genre}' not seen in training data. Using a default encoding.")


                    input_features = [[country_encoded, release_year, rating_encoded, genre_encoded]]
                    pred_encoded = model.predict(input_features)[0]
                    pred_label = le_type.inverse_transform([pred_encoded])[0]

                    st.success(f"🎬 **{title_input}** is predicted to be a **{pred_label}**.")
            except Exception as e:
                st.error(f"⚠️ An error occurred during prediction: {str(e)}")

# Data Table Section
st.markdown("## 📋 Detailed Data")
with st.expander("View Filtered Dataset", expanded=False):
    # Add search functionality
    search_term = st.text_input("🔍 Search titles:", placeholder="Enter movie or show name...")

    if search_term:
        search_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
        st.write(f"Found {len(search_df)} matches for '{search_term}'")
        st.dataframe(search_df, use_container_width=True)
    else:
        st.dataframe(filtered_df, use_container_width=True)

# Insights Section
st.markdown("## 💡 Key Insights")
insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.markdown("""
    <div class="section-header">
        <h3>📈 Content Trends</h3>
        <ul style="color: #cccccc;">
            <li>Netflix has been rapidly expanding its content library</li>
            <li>Original content production has increased significantly</li>
            <li>International content is growing in popularity</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with insight_col2:
    st.markdown("""
    <div class="section-header">
        <h3>🌍 Global Reach</h3>
        <ul style="color: #cccccc;">
            <li>Content spans across multiple countries and cultures</li>
            <li>Diverse rating categories cater to all audiences</li>
            <li>Genre diversity continues to expand</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Feedback CTA
st.markdown(
    """
    <div style='background-color:#1f1f1f; padding:20px; border-radius:10px; text-align:center; margin-bottom: 2rem;'>
        <h3 style='color:#E50914;'>💬 Loved the Dashboard?</h3>
        <p style='color:#cccccc;'>I'd be thrilled to hear what you think! Connect with me on <a href='https://www.linkedin.com/in/sai-sharmi-gade-55710828b/' target='_blank' style='color:#E50914; text-decoration: none;'>LinkedIn</a> and share your feedback!</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(90deg, #1a1a1a 0%, #2a2a2a 100%); border-radius: 10px;">
        <h3 style="color: #E50914; margin-bottom: 1rem;">🎬 Netflix Analytics Dashboard</h3>
        <p style="color: #cccccc; margin: 0;">Built with ❤️ by <strong>Sai Sharmi Gade</strong></p>
        <p style="color: #888; margin: 0.5rem 0 0 0;">Powered by Streamlit & Plotly</p>
    </div>
    """, unsafe_allow_html=True)
