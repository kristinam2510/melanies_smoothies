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
    st.write(f"The name on your smoothie will be: **{name_on_order}**")

# -----------------------------
# Connect to Snowflake
# -----------------------------
cnx = st.connection("snowflake")
session = cnx.session()

fruit_table = (
    session.table("smoothies.public.fruit_options")
    .select(
        col("FRUIT_NAME"),
        col("SEARCH_ON")
    )
)

pd_df = fruit_table.to_pandas()

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
# Nutrition Information
# -----------------------------
if ingredients_list:

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + " "

        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.write(
            f"Searching nutrition information for **{fruit_chosen}** "
            f"using **{search_on}**"
        )

        try:
            response = requests.get(
                f"https://www.smoothiefroot.com/api/fruit/{search_on}"
            )

            data = response.json()

            # Debug (optional)
            # st.write(data)

            st.subheader(f"{fruit_chosen} Nutrition Information")

            if "error" in data:
                st.error(data["error"])

            else:

                # Convert any JSON response into a dataframe
                if isinstance(data, dict):

                    rows = []

                    for key, value in data.items():

                        if isinstance(value, dict):
                            for k, v in value.items():
                                rows.append([k, v])
                        else:
                            rows.append([key, value])

                    nutrition_df = pd.DataFrame(
                        rows,
                        columns=["Attribute", "Value"]
                    )

                    st.dataframe(
                        nutrition_df,
                        use_container_width=True
                    )

                else:
                    st.write(data)

        except Exception as e:
            st.error(f"API Error: {e}")

    # -----------------------------
    # Submit Order
    # -----------------------------
    if st.button("Submit Order"):

        insert_sql = """
        INSERT INTO smoothies.public.orders
        (ingredients, name_on_order)
        VALUES (?, ?)
        """

        session.sql(
            insert_sql,
            params=[
                ingredients_string.strip(),
                name_on_order
            ]
        ).collect()

        st.success("✅ Your Smoothie has been ordered!")
