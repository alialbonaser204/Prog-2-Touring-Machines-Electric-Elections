import os
import pandas as pd
from model import WegModel

os.makedirs("data", exist_ok=True)


def run_simulatie(multi, stappen_max=10000, max_autos=1000, run_index=1):
    model = WegModel(multi=multi, width=15, height=100, num_cars=0)
    model.max_autos = max_autos  # Zorg dat beide modellen gelijk aantal krijgen

    for _ in range(stappen_max):
        model.step()
        if model.aantal_afgereden_autos >= max_autos:
            break

    # 📤 Per-uur data exporteren
    label = "multi" if multi else "single"
    model.exporteer_per_uur_data(f"data/per_uur_data_{label}_run{run_index}.csv")

    df = model.datacollector.get_model_vars_dataframe()
    df["configuratie"] = label
    return df


if __name__ == "__main__":
    aantal_runs = 1

    # Simuleer van 7:00 tot 21:00 = 14 uur = 50.400 seconden/stappen
    duur_uren = 14
    stappen_max = duur_uren * 60 * 60

    # Gemiddelde intensiteit 45 auto's per minuut = 2700 per uur
    # Geef wat marge (0.75 auto's per seconde)
    max_autos = int(duur_uren * 60 * 60 * 0.75)

    alle_runs = []

    for i in range(aantal_runs):
        print(f"🔁 Run {i + 1} - 3 rijbanen (multi)")
        df_multi = run_simulatie(multi=True, stappen_max=stappen_max, max_autos=max_autos)
        df_multi["run"] = i + 1
        alle_runs.append(df_multi)

        print(f"🔁 Run {i + 1} - 1 gecombineerde baan (single)")
        df_single = run_simulatie(multi=False, stappen_max=stappen_max, max_autos=max_autos)
        df_single["run"] = i + 1
        alle_runs.append(df_single)

    resultaten_df = pd.concat(alle_runs)
    resultaten_df.to_csv("data/simulatie_resultaten.csv", index=False)
    print("✅ Resultaten opgeslagen in: data/simulatie_resultaten.csv")
