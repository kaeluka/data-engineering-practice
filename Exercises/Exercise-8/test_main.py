import duckdb
import main

def mk_test_connection() -> duckdb.DuckDBPyConnection:
    return main.create_ev_data_table(duckdb.connect())

def mock_car(City: str = "Eugene", PostalCode: int = 97404, Make: str = "VOLVO", Model: str = "S60") -> list[str]:
    return ["1234567890","Test",City,"OR",PostalCode,2021,Make,Model,"Plug-in Hybrid Electric Vehicle (PHEV)","Not eligible due to low battery range",12,0,0,123456789,"POINT (-1.1 44.4)","","12345678901"]


def test_setup():
    """Test that we can connect to a database and run a query."""
    con = duckdb.connect()
    con.execute("CREATE TABLE test (a INTEGER, b INTEGER);")
    con.execute("INSERT INTO test VALUES (2, 3);")
    result = con.execute("SELECT * FROM test;")

    values = result.fetchdf().values.tolist()

    print(str(values))
    # assert that the values are as expected
    assert values[0][0] == 2
    assert values[0][1] == 3
    con.close()


def test_cars_per_city():
    """Test the count of electric cars per city."""
    con = mk_test_connection()

    mc = mock_car()
    con.execute("INSERT INTO ev_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mc)

    result = main.count_electric_cars_per_city(con)

    values = result.fetchdf().values.tolist()
    assert len(values) == 1, "Expected one city"
    assert values[0][1] == 1, "Expected one car in that city"
    assert values[0][0] == "Eugene", "The city should be Eugene"
    con.close()

def test_most_popular_vehicles():
    """Test the most popular vehicles."""
    con = mk_test_connection()

    mcs = [
        mock_car(Make="VOLVO", Model="S60"),
        mock_car(Make="VOLVO", Model="S60"),
        mock_car(Make="VOLVO", Model="S60"),
        mock_car(Make="VOLVO", Model="S60"),
        mock_car(Make="BMW", Model="X5"),
        mock_car(Make="BMW", Model="X5"),
        mock_car(Make="BMW", Model="X5"),
        mock_car(Make="FORD", Model="FOCUS"),
        mock_car(Make="FORD", Model="FOCUS"),
        mock_car(Make="NISSAN", Model="LEAF"),
    ]
    for mc in mcs:
        con.execute("INSERT INTO ev_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mc)

    N = 3 # get the top 3 vehicles
    result = main.most_popular_vehicles(con, N)

    values = result.fetchdf().values.tolist()
    assert len(values) == N, f"Expected top-{N} vehicles"
    assert values[0][0] == "VOLVO"
    assert values[0][1] == "S60"
    assert values[1][0] == "BMW"
    assert values[1][1] == "X5"
    assert values[2][0] == "FORD"
    assert values[2][1] == "FOCUS"

    con.close()


def test_most_popular_vehicle_by_postal_code():
    con = mk_test_connection()
    mcs = [
        mock_car(PostalCode=123, Make="VOLVO", Model="S60"),
        mock_car(PostalCode=123, Make="VOLVO", Model="S60"),
        mock_car(PostalCode=123, Make="BMW", Model="X5"),
        
        mock_car(PostalCode=234, Make="VOLVO", Model="S60"),
        mock_car(PostalCode=234, Make="BMW", Model="X5"),
        mock_car(PostalCode=234, Make="BMW", Model="X5"),
    ]

    for mc in mcs:
        con.execute("INSERT INTO ev_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mc)
    
    result = main.most_popular_vehicle_by_postal_code(con)
    values = result.fetchdf().values.tolist()

    assert len(values) == 2, "Expected two top vehicles (because there are two postal codes)"

    assert values[0][0] == 123
    assert values[0][1] == "VOLVO"
    assert values[0][2] == "S60"
    assert values[0][3] == 2

    assert values[1][0] == 234
    assert values[1][1] == "BMW"
    assert values[1][2] == "X5"
    assert values[1][3] == 2
        
