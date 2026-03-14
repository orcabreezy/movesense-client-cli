import click


@click.command()
@click.option("--count", help="Number of greetings.")
@click.option("--name", prompt="Your Name", help="The person greeting.")
def hello(count, name):
    click.echo(f"Hello {name}! + {count}")


if __name__ == "__main__":
    hello()
