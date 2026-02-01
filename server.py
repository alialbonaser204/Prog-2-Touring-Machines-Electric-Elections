from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid

from model import WegModel, Stoplicht, AgentAuto

def draw_agent(agent):
    # Tekent stoplichten en auto's op het grid
    if isinstance(agent, Stoplicht):
        color = "green" if agent.status == "Groen" else "red"
        return {
            "Shape": "rect",
            "Filled": "true",
            "Color": color,
            "w": 1,
            "h": 1,
            "Layer": 0
        }

    elif isinstance(agent, AgentAuto):
        color = "pink" if agent.kleur == "Roze" else "black" if agent.kleur == "Zwart" else "blue"
        return {
            "Shape": "circle",
            "Filled": "true",
            "Color": color,
            "r": 0.5,  # Straal van de cirkel
            "Layer": 1
        }

# Configuratie van de gridvisualisatie
grid = CanvasGrid(draw_agent, 15, 100, 500, 500)

# Start de server met de WegModel
server = ModularServer(
    WegModel,
    [grid],
    "Verkeerssimulatie WegModel",  # Titel van de simulatie
    {
        'multi': True,    # Multi-modus ingeschakeld
        'width': 15,      # Breedte van de grid
        'height': 100,    # Hoogte van de grid
        'num_cars': 5     # Start met 5 auto's
    }
)

# Start de server
server.port = 8521  # Verander poort als nodig
server.launch()
