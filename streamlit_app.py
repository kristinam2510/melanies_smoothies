import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# -----------------------------
# Page Title
# -----------------------------
st.title("Customize Your Smoothie 🥤")
st.write("Choose the fruits you want in your custom Smoothie!")

# -----------------------------
# Customer Name
# -----------------------------
name_on_order = st.text_input("Name on Smoothie")

if name_on_order:
    st.write("The name of your smoothie will be:", name_on_order)

# -----------------------------
# Connect to Snowflake
# -----------------------------
cnx = st.connection("snowflake")
session = cnx.session()

# -----------------------------
# Read Fruit Options
# -----------------------------
fruit_df = (
    session.table("smoothies.public.fruit_options")
    .select(
        col("FRUIT_NAME"),
        col("SEARCH_ON")
    )
    .to_pandas()
)

# -----------------------------
# Fruit Selection
# -----------------------------
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

# -----------------------------
# Display Nutrition Information
# -----------------------------
ingredients_string = ""

if ingredients_list:

    ingredients_string = " ".join(ingredients_list)

    for fruit in ingredients_list:

        search_on = fruit_df.loc[
            fruit_df["FRUIT_NAME"] == fruit,
            "SEARCH_ON"
        ].iloc[0]

        st.subheader(f"{fruit} Nutrition Information")

        url = f"https://fruityvice.com/api/fruit/{search_on}"

        try:
            response = requests.get(url)

            if response.status_code == 200:

                fruit_data = response.json()

                nutrition = fruit_data["nutritions"]

                nutrition_df = pd.DataFrame(
                    {
                        "Nutrition": nutrition.keys(),
                        "Value": nutrition.values()
                    }
                )

                st.dataframe(
                    nutrition_df,
                    use_container_width=True
                )

            else:
                st.error(f"Could not retrieve nutrition data for {fruit}")

        except Exception as e:
            st.error(e)

# -----------------------------
# Submit Order
# -----------------------------
if st.button("Submit Order"):

    if name_on_order == "":
        st.warning("Please enter your name.")
    elif len(ingredients_list) == 0:
        st.warning("Please choose at least one fruit.")
    else:

        session.sql(
            """
            INSERT INTO smoothies.public.orders
            (ingredients, name_on_order)
            VALUES (?, ?)
            """,
            params=[ingredients_string, name_on_order]
        ).collect()

        st.success("✅ Your Smoothie is ordered!")
