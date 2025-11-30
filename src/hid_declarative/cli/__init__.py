import sys

# 1. On initialise app à None par défaut (pour le cas sans dépendances)
app = None

try:
    import typer
    # Attention: 'list' est un mot clé réservé Python, on l'alias
    from .commands import inspect, decode, encode, live, dump, list as list_cmd, compile

    # 2. Si Typer est là, on construit l'app GLOBALE
    app = typer.Typer(
        help="HID Declarative CLI",
        add_completion=False,
        no_args_is_help=True
    )

    # 3. On enregistre les commandes tout de suite
    app.command(name="inspect")(inspect.main)
    app.command(name="decode")(decode.main)
    app.command(name="encode")(encode.main)
    app.command(name="live")(live.main)
    app.command(name="dump")(dump.main)
    app.command(name="list")(list_cmd.main)
    app.command(name="compile")(compile.main)

except ImportError as e:
    # Si les dépendances manquent, app reste None
    print(f"[WARNING] CLI dependencies are missing: {e}")
    pass

def main():
    """Point d'entrée pour le script console."""
    # 4. Le main ne fait que lancer l'app si elle existe
    if app is None:
        print("\n[ERROR] CLI dependencies are missing.")
        print("Please install them using: pip install 'hid-declarative[cli]'\n")
        sys.exit(1)
    
    app()