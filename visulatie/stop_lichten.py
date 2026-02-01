from mesa.agent import Agent


class Stoplicht(Agent):
    def __init__(self, unique_id, model, richting, multi):
        super().__init__(model=model, unique_id=unique_id)
        self.unique_id = unique_id
        self.richting = richting  # bijv. "links", "rechts", "rechtdoor" of "alle"
        self.multi = multi
        self.status = 'Red'  # Initieel
        self.is_groen = False  # Deze kun je gebruiken voor visuele interface of logging

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
