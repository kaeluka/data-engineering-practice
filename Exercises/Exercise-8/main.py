import duckdb
import re

def create_ev_data_table(con: duckdb.DuckDBPyConnection):
    """
    Create a table for the Electric Vehicle Population Data.
    """
    return con.execute(
        """
        CREATE TABLE ev_data (
          "VIN (1-10)" varchar not null check(length("VIN (1-10)") = 10), -- duckdb ignores the length in char(10)
          County varchar not null,
          City varchar not null,
          State varchar not null,
          "Postal Code" integer not null,
          "Model Year" smallint not null,
          Make varchar not null,
          Model varchar, -- NULLABLE!
          "Electric Vehicle Type" varchar not null,
          "Clean Alternative Fuel Vehicle (CAFV) Eligibility" varchar not null,
          "Electric Range" integer not null,
          "Base MSRP" integer not null,
          "Legislative District" integer, -- NULLABLE!
          "DOL Vehicle ID" integer not null,
          "Vehicle Location" varchar, -- NULLABLE!
          "Electric Utility" varchar, -- NULLABLE!
          "2020 Census Tract" varchar not null,
        );
        """
    )

def read_csv(con: duckdb.DuckDBPyConnection, path: str) -> duckdb.DuckDBPyConnection:
    """
    Read an Electric Vehicle Population Data CSV file into a Connection.
    """

    # Sanitize the path.
    # XXX This is erring on the strict side, but it works for our data.
    # Could consider using something more robust here.
    if not re.match("[a-zA-Z/_0-9]+[.]csv$", path):
        raise ValueError("Invalid path to CSV file")

    return con.execute(
        f"""
        insert into ev_data
        select * from '{path}';
        """)

def count_electric_cars_per_city(con: duckdb.DuckDBPyConnection):
    """
    Returns the number of electric cars per city in the dataset.
    """
    return con.execute("""
    select City, State, "Postal Code", Count(*) as Count from ev_data
    group by City, State, "Postal Code"
    order by Count desc;
    """)

def most_popular_vehicles(con: duckdb.DuckDBPyConnection, limit: int = 3):
    """
    Returns the most popular vehicles in the dataset.

    Parameters
    ----------
    limit : int, optional
        The number of vehicles to return, by default 3.
    """
    return con.execute("""
    select Make, Model, COUNT(*) as Count from ev_data
    group by Make, Model
    order by Count desc
    limit $limit;
    """, parameters={"limit": limit})

def most_popular_vehicle_by_postal_code(con: duckdb.DuckDBPyConnection):
    """
    Returns the most popular vehicle in each postal code in the dataset, ordered
    by postal code.

    Will return multiple vehicles per postal code if there is a tie.
    """

    return con.execute("""
    select "Postal Code", Make, Model, Count from (
        select "Postal Code", Make, Model, Count, Max(Count) over (partition by "Postal Code") as MaxCount from
        (
            select "Postal Code", Make, Model, Count(*) as Count from ev_data
            group by "Postal Code", Make, Model
        )
    )
    where Count = MaxCount
    order by Count desc, "Postal Code" asc, Make asc, Model asc;
    """)

def vehicles_by_model_year(con: duckdb.DuckDBPyConnection):
    """
    Returns the number of vehicles by model year.
    """
    return con.execute("""
    select "Model Year", COUNT(*) as Count from ev_data
    group by "Model Year"
    order by "Model Year" asc;
    """)


def main():
    con = duckdb.connect()
    create_ev_data_table(con)

    read_csv(con, "data/Electric_Vehicle_Population_Data.csv")

    print("The number of electric cars per city is:")
    print(count_electric_cars_per_city(con).fetchdf().to_string())

    print("The three most popular vehicles are:")
    print(most_popular_vehicles(con, 3).fetchdf().to_string())

    print("Most popular vehicle by postal code:")
    print(most_popular_vehicle_by_postal_code(con).fetchdf().to_string())

    print("Vehicles by model year:")
    vbmy = vehicles_by_model_year(con).fetch_df()
    vbmy.to_parquet("vehicles_by_model_year.parquet")
    print(vbmy.to_string())

    con.close()


if __name__ == "__main__":
    main()
