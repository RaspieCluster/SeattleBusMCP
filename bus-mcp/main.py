from server import mcp

def run_server():
    print("Hello from bus-mcp!")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    run_server()
