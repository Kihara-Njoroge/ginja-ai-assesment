from app.main import create_app


def print_routes():
    app = create_app()
    for route in app.routes:
        print(
            f"Path: {getattr(route, 'path', 'No Path')} | Methods: {getattr(route, 'methods', 'No Methods')} | Name: {getattr(route, 'name', 'No Name')}"
        )


if __name__ == "__main__":
    print_routes()
