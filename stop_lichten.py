

# from mesa import Agent
# we gebruiken onze eigen veilige agent
from safe_agent import SafeAgent as Agent

class Stoplicht(Agent):
    def __init__(self, unique_id, model, richting, multi):
        # Gebruik GEEN super() meer, maar roep direct de Agent.__init__ aan
        Agent.__init__(self, unique_id, model)  # <-- dit werkt altijd!

        self.richting = richting  # bijv. "links", "rechts", "rechtdoor" of "alle"
        self.multi = multi
        self.status = 'Red'  # Initieel
        self.is_groen = False  # Voor visualisatie/logging

    def advance(self):
        pass

    def step(self):
        # In deze implementatie bepaalt het model elke stap wie groen krijgt
        # Deze functie wordt dus hier niet gebruikt tenzij je zelf cycli per stoplicht doet
        pass

    def is_groen_voor_richting(self, richting_auto):
        """
        Geeft aan of een auto met een bepaalde richting door dit stoplicht mag.
        Bij 'single lane' (multi=False) is richting minder belangrijk.
        """
        if not self.multi:
            return self.status == "Groen"  # iedereen mag tegelijk
        return self.status == "Groen" and self.richting == richting_auto