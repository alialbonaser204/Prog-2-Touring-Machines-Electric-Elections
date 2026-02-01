from safe_agent import SafeAgent as Agent

from stop_lichten import Stoplicht
import random

class AgentAuto(Agent):
    def __init__(self, unique_id, model, kleur=None, afstand_factor=2, snelheid=None, versnelling=None):
        Agent.__init__(self, unique_id, model)

        self.unique_id = unique_id
        self.kleur = kleur if kleur else self._random_kleur()
        self.richting = self._koppel_richting_aan_kleur()
        self.afstand_factor = afstand_factor
        self.gestopt = False
        self.pos = None

        self.type = self._bepaal_type()

        if snelheid is not None and versnelling is not None:
            self.snelheid = snelheid
            self.versnelling = versnelling
        else:
            self._stel_type_eigenschappen_in()

        self.wachttijd = 0

        self.step_gestopt_op_rood = False


    def _bepaal_type(self):
        r = random.random()
        if r < 0.7:
            return "auto"
        elif r < 0.9:
            return "vrachtwagen"
        else:
            return "bus"

    def _stel_type_eigenschappen_in(self):
        if self.type == "auto":
            self.snelheid = random.uniform(35, 55)
            self.versnelling = random.uniform(2.0, 3.0)
        elif self.type == "vrachtwagen":
            self.snelheid = random.uniform(30, 45)
            self.versnelling = random.uniform(1.0, 1.8)
        elif self.type == "bus":
            self.snelheid = random.uniform(30, 50)
            self.versnelling = random.uniform(1.2, 2.0)

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
        nieuwe_snelheid_ms = self.snelheid_in_ms() + self.versnelling * tijd
        self.snelheid = min(nieuwe_snelheid_ms * (3600 / 1000), 50)

        beweging = self.stapgrootte_in_grids()
        x, y = self.pos
        nieuwe_y = y + beweging

        # Controleer of nieuwe_y binnen de gridgrenzen valt
        if nieuwe_y >= self.model.grid.height:
            #  Altijd wachttijd opslaan
            self.model.aantal_afgereden_autos += 1
            self.model.wachttijden.append(self.wachttijd)

            #  Richting veilig verwerken
            richting = self.richting if self.richting in self.model.afgereden_per_richting else "rechtdoor"
            self.model.afgereden_per_richting[richting] += 1
            self.model.wachttijd_per_richting[richting].append(self.wachttijd)


            # Pas daarna verwijderen
            if self in self.model.schedule.agents:
                self.model.schedule.remove(self)
            if self.pos and self in self.model.grid.get_cell_list_contents([self.pos]):
                self.model.grid.remove_agent(self)

            return

        # Reset wachttijd increment
        self.wachttijd_incr = 0

        # === STOP VOOR ROOD LICHT ===
        kijk_y = y + 1
        if kijk_y < self.model.grid.height:
            kijk_positie = (x, kijk_y)
            agents_op_voorgrond = self.model.grid.get_cell_list_contents([kijk_positie])
            stoplicht_in_weg = next((a for a in agents_op_voorgrond if isinstance(a, Stoplicht)), None)

            if stoplicht_in_weg:
                # Altijd checken of stoplicht groen is voor deze auto
                if not stoplicht_in_weg.is_groen_voor_richting(self.richting):
                    self.gestopt = True
                    self.wachttijd_incr = 1

        # === CHECK ANDERE AUTO'S BINNEN AFSTAND ===
        for i in range(1, self.model.afstand_vooruit + 1):
            check_y = y + i
            if check_y >= self.model.grid.height:
                break
            inhoud = self.model.grid.get_cell_list_contents([(x, check_y)])
            for agent in inhoud:
                if isinstance(agent, AgentAuto) and agent.gestopt:
                    self.gestopt = True
                    self.wachttijd_incr = 1  # Markering voor increment

        # === NORMAAL BEWEGEN ===
        if self.model.grid.is_cell_empty((x, nieuwe_y)) and self.wachttijd_incr == 0:
            self.model.grid.move_agent(self, (x, nieuwe_y))
            self.gestopt = False
        else:
            self.gestopt = True if self.wachttijd_incr > 0 else False

        # Voeg wachttijd toe na alle checks
        if self.wachttijd_incr > 0:
            self.wachttijd += self.wachttijd_incr
            self.wachttijd_incr = 0  # Reset

    def advance(self):
        pass
