from mesa.agent import Agent
from stop_lichten import Stoplicht
import random


class AgentAuto(Agent):
    def __init__(self, unique_id, model, afstand_factor=2, snelheid=None, versnelling=None):
        super().__init__(model=model, unique_id=unique_id)
        self.unique_id = unique_id
        self.kleur = self._random_kleur()
        self.richting = self._koppel_richting_aan_kleur()
        self.afstand_factor = afstand_factor

        self.type = self._bepaal_type()

        self.snelheid = snelheid
        self.versnelling = versnelling

        self.wachttijd = 0
        self.gestopt = False
        self.heeft_bewogen = False

    def _bepaal_type(self):
        r = random.random()
        if r < 0.7:
            return "auto"
        elif r < 0.9:
            return "vrachtwagen"
        else:
            return "bus"

    def _random_kleur(self):
        kans = random.random()
        if kans < 0.15:
            return "Roze"
        elif kans < 0.30:
            return "Zwart"
        else:
            return "Blauw"

    def _koppel_richting_aan_kleur(self):
        if self.kleur == "Roze":
            return "rechts"
        elif self.kleur == "Zwart":
            return "links"
        elif self.kleur == "Blauw":
            return "rechtdoor"

    def snelheid_in_ms(self):
        return self.snelheid * (1000 / 3600)

    def veilige_afstand(self):
        return self.afstand_factor * self.snelheid_in_ms()

    def veilige_afstand_in_grids(self):
        return max(1, round(self.veilige_afstand() / self.model.grid.cell_size))

    def stapgrootte_in_grids(self):
        snelheid_ms = self.snelheid_in_ms()
        return max(1, round(snelheid_ms / 1))

    def step(self):
        tijd = 1
        self.heeft_bewogen = False  # Reset voor deze stap
        nieuwe_snelheid_ms = self.snelheid_in_ms() + self.versnelling * tijd
        self.snelheid = min(nieuwe_snelheid_ms * (3600 / 1000), 50)

        beweging = self.stapgrootte_in_grids()
        x, y = self.pos
        nieuwe_y = y + beweging
        self.gestopt = False  # Reset aan het begin van de stap

        # === STOP VOOR ROOD LICHT ===
        for i in range(1, beweging + 1):
            kijk_y = y + i
            if kijk_y < self.model.grid.height:
                kijk_positie = (x, kijk_y)
                agents_op_voorgrond = self.model.grid.get_cell_list_contents([kijk_positie])
                stoplicht_in_weg = next((a for a in agents_op_voorgrond if isinstance(a, Stoplicht)), None)

                if stoplicht_in_weg:
                    juiste_richting = (
                            not self.model.multi or
                            (self.richting == stoplicht_in_weg.richting)
                    )
                    if juiste_richting and stoplicht_in_weg.status == 'Red':
                        self.gestopt = True
                        self.wachttijd += 1  # Verhoog de wachttijd met 1 per stap
                        return

        # === KRUISPUNT VERLATEN ===
        if nieuwe_y >= self.model.grid.height:
            self.model.aantal_afgereden_autos += 1
            self.model.wachttijden.append(self.wachttijd)

            if self.richting in self.model.afgereden_per_richting:
                self.model.afgereden_per_richting[self.richting] += 1
            self.model.wachttijd_per_richting[self.richting].append(self.wachttijd)

            if self in self.model.schedule.agents:
                self.model.schedule.remove(self)
            if self.pos and self in self.model.grid.get_cell_list_contents([self.pos]):
                self.model.grid.remove_agent(self)
            return

        # === NORMAAL BEWEGEN ===
        if self.model.grid.is_cell_empty((x, nieuwe_y)):
            self.model.grid.move_agent(self, (x, nieuwe_y))
            self.gestopt = False  # Hij beweegt weer, dus niet meer gestopt
            self.heeft_bewogen = True

            # === Afslaan direct ná stoplicht ===
            if self.richting in ["links", "rechts"]:
                x_huidig, y_huidig = self.pos
                if y_huidig > 80:  # eventueel controleren of dit klopt met locatie stoplicht
                    nieuwe_x = x_huidig - 1 if self.richting == "links" else x_huidig + 1
                    if 0 <= nieuwe_x < self.model.grid.width:
                        if self.model.grid.is_cell_empty((nieuwe_x, y_huidig)):
                            self.model.grid.move_agent(self, (nieuwe_x, y_huidig))

        else:
            self.gestopt = True
            self.wachttijd += 1  # Verhoog wachttijd als de auto niet kan bewegen
            return

        if not self.heeft_bewogen:
            self.gestopt = True
            self.wachttijd += 1
