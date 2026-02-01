from collections import defaultdict
import pandas as pd
from mesa import Model
from mesa.space import SingleGrid
from mesa.time import SimultaneousActivation
import random
from stop_lichten import Stoplicht
from auto import AgentAuto
import uuid
from mesa.datacollection import DataCollector


class WegModel(Model):
    def __init__(self, multi, width, height, num_cars):
        super().__init__()
        self.num_agents = num_cars
        self.grid = SingleGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.multi = multi

        self.stoplichten = self.plaats_stoplicht(3 if multi else 1)
        self._id_counter = 0
        self.time_step = 0

        # 🔁 Stoplicht-cyclus instellen
        if self.multi:
            self.stoplicht_verdeling = {
                "rechts": 15,
                "links": 15,
                "rechtdoor": 70
            }
            self.cyclustijd = sum(self.stoplicht_verdeling.values())  # 100 sec
        else:
            self.cyclustijd = 200  # 100 sec groen per richting

        self.spawn_interval = 36  # Gemiddeld aantal auto's per minuut

        self.aantal_afgereden_autos = 0
        self.wachttijden = []
        self.max_autos = 1000
        self.autos_geteld = 0
        self.afstand_vooruit = 2
        self.spits = True
        self.intensiteit_per_min = 0
        self.afgereden_per_richting = {
            "rechts": 0,
            "links": 0,
            "rechtdoor": 0
        }
        self.wachttijd_per_richting = {
            "rechts": [],
            "links": [],
            "rechtdoor": []
        }
        self.per_uur_data = defaultdict(lambda: {
            "afgereden": 0,
            "gem_wachttijd": 0,
            "aantal_autos": 0,
            "wachttijd_rechts": 0,
            "wachttijd_links": 0,
            "wachttijd_rechtdoor": 0
        })

        self.spawn_queue = []

        self.init_autos()

        self.datacollector = DataCollector(
            model_reporters={
                "AantalAfgeredenAutos": lambda m: m.aantal_afgereden_autos,
                "GemiddeldeWachttijd": lambda m: (
                    sum(m.wachttijden) / len(m.wachttijden) if m.wachttijden else 0
                ),
                "AantalActieveAutos": lambda m: len([
                    a for a in m.schedule.agents if isinstance(a, AgentAuto)
                ]),
                "AfgeredenRechts": lambda m: m.afgereden_per_richting["rechts"],
                "AfgeredenLinks": lambda m: m.afgereden_per_richting["links"],
                "AfgeredenRechtdoor": lambda m: m.afgereden_per_richting["rechtdoor"]
            }
        )

    def plaats_stoplicht(self, num_stoplichten):
        stoplichten = []
        if self.multi:
            posities = [(6, 80), (8, 80), (10, 80)]
            richtingen = ["links", "rechtdoor", "rechts"]

            for i in range(num_stoplichten):
                richting = richtingen[i]
                pos = posities[i]
                stoplicht = Stoplicht(i, self, richting, self.multi)
                stoplichten.append(stoplicht)
                self.schedule.add(stoplicht)
                self.grid.place_agent(stoplicht, pos)
        else:
            stoplicht = Stoplicht(0, self, "alle", self.multi)
            self.schedule.add(stoplicht)
            self.grid.place_agent(stoplicht, (7, 10))
            stoplichten.append(stoplicht)

        return stoplichten

    def generate_next_id(self):
        return str(uuid.uuid4())

    def init_autos(self):
        for _ in range(self.num_agents):
            self.spawn_auto()

    def spawn_auto(self):
        if self.autos_geteld >= self.max_autos:
            return

        y_offset = 31
        snelheid = random.uniform(15, 50)
        versnelling = random.uniform(2, 6)

        auto = AgentAuto(
            unique_id=self.generate_next_id(),
            model=self,
            snelheid=snelheid,
            versnelling=versnelling
        )

        if self.multi:
            if auto.richting == "links":
                stoplicht = self.stoplichten[0]
            elif auto.richting == "rechtdoor":
                stoplicht = self.stoplichten[1]
            else:
                stoplicht = self.stoplichten[2]
        else:
            stoplicht = self.stoplichten[0]

        x = stoplicht.pos[0]
        y = y_offset

        x = min(self.grid.width - 1, max(0, x))
        y = min(self.grid.height - 5, max(0, y))

        while not self.grid.is_cell_empty((x, y)):
            y += 1
            if y >= self.grid.height - 1:
                return

        self.schedule.add(auto)
        self.grid.place_agent(auto, (x, y))
        self.autos_geteld += 1

    def exporteer_per_uur_data(self, pad="data/per_uur_data.csv"):
        import pandas as pd

        data_lijst = []
        for uur, waarden in self.per_uur_data.items():
            rij = {"uur": uur}
            rij.update(waarden)
            data_lijst.append(rij)

        df = pd.DataFrame(data_lijst)
        df.to_csv(pad, index=False)
        print(f"📤 Per-uur data opgeslagen in: {pad}")

    def exporteer_gemiddelde_wachttijd(self, bestand):
        df = pd.DataFrame({
            "gemiddelde": [sum(self.wachttijden) / len(self.wachttijden)] if self.wachttijden else [0],
            "minimum": [min(self.wachttijden)] if self.wachttijden else [0],
            "maximum": [max(self.wachttijden)] if self.wachttijden else [0],
            "aantal_autos": [len(self.wachttijden)]
        })
        df.to_csv(bestand, index=False)

    def Finalize(self):
        for agent in self.schedule.agents:
            if isinstance(agent, AgentAuto):
                self.wachttijden.append(agent.wachttijd)
                richting = agent.richting
                if richting in self.afgereden_per_richting:
                    self.afgereden_per_richting[richting] += 1
                else:
                    richting = "rechtdoor"  # fallback
                self.wachttijd_per_richting[richting].append(agent.wachttijd)
        print(f"✅ Finalized met {len(self.wachttijden)} wachttijden")

    def step(self):
        self.schedule.step()
        self.time_step += 1

        if self.time_step % 60 == 0:
            if self.spits:
                aantal = random.randint(15, 30) if not self.multi else random.randint(60, 85)  # Verhoog spawn rate
            else:
                aantal = random.randint(5, 15) if not self.multi else random.randint(15, 40)

            self.spawn_queue = [True] * aantal + [False] * (60 - aantal)
            random.shuffle(self.spawn_queue)

        if self.spawn_queue:
            spawn = self.spawn_queue.pop(0)
            if spawn and self.autos_geteld < self.max_autos:
                self.spawn_auto()

        # Verkeerslichtlogica
        if self.multi:
            offset = self.time_step % self.cyclustijd
            som = 0
            actieve_richting = None

            for richting in ["links", "rechtdoor"]:  # Geen 'rechts', die koppelen we aan 'rechtdoor'
                duur = self.stoplicht_verdeling[richting]
                if som <= offset < som + duur:
                    actieve_richting = richting
                    break
                som += duur

            for sl in self.stoplichten:
                if actieve_richting == "rechtdoor":
                    if sl.richting in ["rechtdoor", "rechts", "tegen-rechts"]:
                        sl.status = "Groen"
                    else:
                        sl.status = "Red"
                elif actieve_richting == "links":
                    if sl.richting in ["links", "tegen-links"]:
                        sl.status = "Groen"
                    else:
                        sl.status = "Red"

        else:
            offset = self.time_step % self.cyclustijd
            status = "Groen" if offset < 100 else "Red"
            for sl in self.stoplichten:
                sl.status = status

        if self.time_step % 3600 == 0:  # elke 3600 stappen = 1 uur
            uur = self.time_step // 3600
            afgereden = self.aantal_afgereden_autos

            self.per_uur_data[uur]["afgereden"] = afgereden

            # 🔍 Wachttijd per richting
            for richting in ["rechts", "links", "rechtdoor"]:
                wachttijden = self.wachttijd_per_richting[richting]
                self.per_uur_data[uur][f"wachttijd_{richting}"] = (
                    sum(wachttijden) / len(wachttijden) if wachttijden else 0
                )
                self.wachttijd_per_richting[richting] = []  # resetten voor volgend uur

        self.datacollector.collect(self)
