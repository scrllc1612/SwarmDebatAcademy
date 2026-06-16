from Evaluation.toulmin_score import ToulminScorer
from Utils.debate_reloader import SavedDebateLoader

loader = SavedDebateLoader()
scorer = ToulminScorer()

debate = loader.load_as_debate_state(
    "Experiments/a9e4c176-bd5e-42d6-8454-1a236f79dbec.json"
)

results = scorer.score_debate(debate)

print("\n")
print("=" * 80)
print("MÉTRICAS POR RONDA")
print("=" * 80)

for round_result in results["rounds"]:

    print("\n")
    print(f"RONDA {round_result['round_number']}")

    print("\nPRO")
    print(
        f"Score: "
        f"{round_result['pro']['argument_score_100']:.2f}"
    )

    print(
        f"Claim: "
        f"{round_result['pro']['claim_quality']['score'] * 100:.2f}"
    )

    print(
        f"Data: "
        f"{round_result['pro']['data_relevance']['score'] * 100:.2f}"
    )

    print(
        f"Warrant: "
        f"{round_result['pro']['warrant_strength']['score'] * 100:.2f}"
    )

    print(
        f"Backing: "
        f"{round_result['pro']['backing_adequacy']['score'] * 100:.2f}"
    )

    print(
        f"Rebuttal: "
        f"{round_result['pro']['rebuttal_effectiveness']['score'] * 100:.2f}"
    )

    print("\nCONTRA")

    print(
        f"Score: "
        f"{round_result['contra']['argument_score_100']:.2f}"
    )

    print(
        f"Claim: "
        f"{round_result['contra']['claim_quality']['score'] * 100:.2f}"
    )

    print(
        f"Data: "
        f"{round_result['contra']['data_relevance']['score'] * 100:.2f}"
    )

    print(
        f"Warrant: "
        f"{round_result['contra']['warrant_strength']['score'] * 100:.2f}"
    )

    print(
        f"Backing: "
        f"{round_result['contra']['backing_adequacy']['score'] * 100:.2f}"
    )

    print(
        f"Rebuttal: "
        f"{round_result['contra']['rebuttal_effectiveness']['score'] * 100:.2f}"
    )

print("\n")
print("=" * 80)
print("RESULTADO GLOBAL")
print("=" * 80)

print(
    f"TQS: {results['average_argument_score_100']:.2f}"
)

print(
    f"SC: "
    f"{results['global_coherence']['global_coherence_score_100']:.2f}"
)

print(
    f"DEBATE SCORE: "
    f"{results['debate_score_100']:.2f}"
)