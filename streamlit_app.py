import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# -----------------------------
# Page Title
# -----------------------------
st.title("🥤 Customize Your Smoothie")
st.write("Choose the fruits you want in your custom smoothie!")

# -----------------------------
# Customer Name
# -----------------------------
name_on_order = st.text_input("Name on Smoothie:")

if name_on_order:
    st.write(f"The name on your smoothie will be **{name_on_order}**.")

# -----------------------------
# Connect to Snowflake
# -----------------------------
cnx = st.connection("snowflake")
session = cnx.session()

fruit_df = (
    session.table("smoothies.public.fruit_options")
    .select(
        col("FRUIT_NAME"),
        col("SEARCH_ON")
    )
)

# Convert Snowpark DataFrame to Pandas
pd_df = fruit_df.to_pandas()

# -----------------------------
# Fruit Selection
# -----------------------------
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

ingredients_string = ""

# -----------------------------
# Display Nutrition Information
# -----------------------------
if ingredients_list:

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + " "

        # Get API search value
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.write(
            f"Searching nutrition information for **{fruit_chosen}** "
            f"using search value **{search_on}**."
        )

        # Call API
        response = requests.get(
            f"https://www.smoothiefroot.com/api/fruit/{search_on}"
        )

        if response.status_code == 200:

            data = response.json()

            if "error" in data:
                st.error(
                    f"No nutrition information was found for {fruit_chosen}."
                )

            else:
                st.subheader(f"{fruit_chosen} Nutrition Information")

                # Fruit details
                st.write(f"**Scientific Name:** {data['name']}")
                st.write(f"**Genus:** {data['genus']}")
                st.write(f"**Family:** {data['family']}")
                st.write(f"**Order:** {data['order']}")

                # Nutrition Table
                nutrition_df = pd.DataFrame(
                    data["nutritions"].items(),
                    columns=["Nutrient", "Amount"]
                )

                st.dataframe(
                    nutrition_df,
                    use_container_width=True
                )

        else:
            st.error(f"Unable to retrieve data for {fruit_chosen}.")

    # -----------------------------
    # Submit Order
    # -----------------------------
    if st.button("Submit Order"):

        session.sql(
            """
            INSERT INTO smoothies.public.orders
            (ingredients, name_on_order)
            VALUES (?, ?)
            """,
            params=[
                ingredients_string.strip(),
                name_on_order
            ]
        ).collect()

        st.success("✅ Your smoothie has been ordered!")
