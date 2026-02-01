from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.modules import CanvasGrid
from model import WegModel, Stoplicht, AgentAuto


def draw_agent(agent):
    """Returnt een visualisatievoorstelling van een agent (stoplicht of auto)."""
    if isinstance(agent, Stoplicht):
        return {
            "Shape": "rect",
            "Filled": True,
            "Color": "green" if agent.status == "Groen" else "red",
            "w": 1,
            "h": 1,
            "Layer": 0
        }

    if isinstance(agent, AgentAuto):
        kleur_map = {
            "Roze": "pink",
            "Zwart": "black",
            "Blauw": "blue"
        }
        return {
            "Shape": "circle",
            "Filled": True,
            "Color": kleur_map.get(agent.kleur, "gray"),
            "r": 1.5,
            "Layer": 1
        }


# ── Configuratie ──────────────────────────────
grid_width = 15
grid_height = 100
canvas_px = 500

grid = CanvasGrid(draw_agent, grid_width, grid_height, canvas_px, canvas_px)

chart = ChartModule([
    {"Label": "GemiddeldeWachttijd", "Color": "Red"}
], data_collector_name='datacollector')

server = ModularServer(
    WegModel,
    [grid, chart],
    "Verkeerssimulatie WegModel",
    {
        "multi": True,
        "width": grid_width,
        "height": grid_height,
        "num_cars": 5
    }
)

server.port = 8521
server.launch()
