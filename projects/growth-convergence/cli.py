import os

import convergence as conv

# menu driven entry point for the whole project, run directly: python cli.py

PLOT_PATH = os.path.join(os.path.dirname(__file__), "convergence_plot.png")


def run_regression_summary():
    # the headline result: does starting income predict growth rate
    rows = conv.add_growth_fields(conv.load_countries())
    result = conv.run_regression(rows)
    print(f"\n{len(rows)} countries, {conv.START_YEAR}-{conv.END_YEAR}")
    print(conv.interpret(result))
    print(
        "\na negative slope means poorer countries grew faster on average, "
        "which is what 'convergence' means here. a positive slope would mean "
        "the income gap widened instead."
    )


def run_weighted_comparison():
    # robustness check: does the answer change if big countries count more
    # than tiny ones? unweighted treats Nauru and China as one data point
    # each, this weights each country by its 1990 population instead, so
    # it's really asking about people converging rather than countries
    rows = conv.add_growth_fields(conv.load_countries())
    unweighted = conv.run_regression(rows)
    weighted = conv.run_population_weighted_regression(rows)

    print(f"\n{len(rows)} countries, {conv.START_YEAR}-{conv.END_YEAR}")
    print("\nunweighted (one country, one vote):")
    print(conv.interpret(unweighted))
    print("\npopulation-weighted (one person, one vote):")
    print(conv.interpret(weighted))
    print(
        "\nif the weighted slope is more negative and R-squared is higher, "
        "it means convergence looks stronger once you count by people "
        "instead of by country, mostly a China and India effect."
    )


def show_rankings():
    # concrete, readable version of the same story: actual countries,
    # actual numbers, not just a coefficient
    rows = conv.add_growth_fields(conv.load_countries())
    top, bottom = conv.top_and_bottom_growers(rows, n=10)

    print(f"\nfastest growing, {conv.START_YEAR}-{conv.END_YEAR}:")
    for r in top:
        print(f"  {r['country']:28s} {r['growth_rate']*100:5.2f}%/yr   ${r['gdp_1990']:>9,.0f} -> ${r['gdp_2023']:>9,.0f}")

    print(f"\nslowest growing (or shrinking):")
    for r in reversed(bottom):
        print(f"  {r['country']:28s} {r['growth_rate']*100:5.2f}%/yr   ${r['gdp_1990']:>9,.0f} -> ${r['gdp_2023']:>9,.0f}")


def make_plot():
    # saves the scatter plot with the fitted line to disk
    rows = conv.add_growth_fields(conv.load_countries())
    result = conv.run_regression(rows)
    conv.plot_convergence(rows, result, PLOT_PATH)
    print(f"\nsaved plot to {PLOT_PATH}")


def refresh_live_data():
    # re-pulls the dataset from the World Bank API instead of using the
    # bundled snapshot, needs internet access on the machine running this
    import fetch_data
    try:
        dataset = fetch_data.build_dataset()
    except RuntimeError as error:
        print(f"\n{error}")
        return
    with open(fetch_data.OUT_PATH, "w", encoding="utf-8") as handle:
        import json
        json.dump(dataset, handle, indent=2)
    print(f"\nrefreshed {fetch_data.OUT_PATH} with {len(dataset)} countries")


def main():
    menu = {
        "1": ("run the convergence regression and see the headline result", run_regression_summary),
        "2": ("see the fastest growing and slowest growing countries", show_rankings),
        "3": ("save the convergence scatter plot", make_plot),
        "4": ("refresh the dataset from the live World Bank API (needs internet)", refresh_live_data),
        "5": ("robustness check: unweighted vs population-weighted", run_weighted_comparison),
    }

    while True:
        print("\ngrowth convergence tracker")
        for key, (label, _) in menu.items():
            print(f"  {key}. {label}")
        print("  6. quit")

        choice = input("> ").strip()
        if choice == "6":
            break
        action = menu.get(choice)
        if action:
            action[1]()
        else:
            print("not a valid choice")


if __name__ == "__main__":
    main()
