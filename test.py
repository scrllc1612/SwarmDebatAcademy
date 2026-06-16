from Swarm.swarm_controller import SwarmController

from Evaluation.toulmin_score import ToulminScorer

from Storage.debate_storage import DebateStorage
from Storage.debate_exporter import DebateExporter


# =====================================
# GENERAR DEBATE
# =====================================

controller = SwarmController()

debate = controller.generate_debate(
    topic="Se debe regular la IA en el ámbito estudiantil"
)


# =====================================
# EVALUAR DEBATE
# =====================================

scorer = ToulminScorer()

results = scorer.score_debate(
    debate
)


# =====================================
# EXPORTAR
# =====================================

exported_debate = DebateExporter.export(
    debate=debate,
    metrics=results,
    system="swarm",
    model_name="gpt-4o-mini"
)


# =====================================
# GUARDAR
# =====================================

storage = DebateStorage()

path = storage.save(
    exported_debate
)


# =====================================
# MOSTRAR DEBATE
# =====================================

print("\n")
print("=" * 80)
print("DEBATE GENERADO")
print("=" * 80)

print(f"Tema: {debate.topic}")
print(f"ID: {debate.debate_id}")

for round_obj in debate.rounds:

    print("\n")
    print("=" * 80)
    print(f"RONDA {round_obj.round_number}")
    print("=" * 80)

    print("\n[PRO]")
    print(round_obj.pro_argument.speech)

    print("\n[CONTRA]")
    print(round_obj.contra_argument.speech)

    print("\n[MODERADOR]")
    print(
        round_obj.moderator_summary.model_dump_json(
            indent=4
        )
    )


# =====================================
# METRICAS POR RONDA
# =====================================

print("\n")
print("=" * 80)
print("METRICAS POR RONDA")
print("=" * 80)

for round_result in results["rounds"]:

    print("\n")
    print("=" * 80)
    print(
        f"RONDA {round_result['round_number']}"
    )
    print("=" * 80)

    print("\nPRO")

    print(
        f"Score Toulmin: "
        f"{round_result['pro']['argument_score_100']:.2f}"
    )

    print(
        f"Claim: "
        f"{round_result['pro']['claim_quality']['score'] * 100:.2f}"
    )

    print(
        f"Data Relevance: "
        f"{round_result['pro']['data_relevance']['score'] * 100:.2f}"
    )

    print(
        f"Data Sufficiency: "
        f"{round_result['pro']['data_sufficiency']['score'] * 100:.2f}"
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
        f"Score Toulmin: "
        f"{round_result['contra']['argument_score_100']:.2f}"
    )

    print(
        f"Claim: "
        f"{round_result['contra']['claim_quality']['score'] * 100:.2f}"
    )

    print(
        f"Data Relevance: "
        f"{round_result['contra']['data_relevance']['score'] * 100:.2f}"
    )

    print(
        f"Data Sufficiency: "
        f"{round_result['contra']['data_sufficiency']['score'] * 100:.2f}"
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

    print("\nPROMEDIO RONDA")

    print(
        f"{round_result['round_average_100']:.2f}"
    )


# =====================================
# RESULTADO GLOBAL
# =====================================

print("\n")
print("=" * 80)
print("RESULTADO GLOBAL")
print("=" * 80)

print(
    f"TQS: "
    f"{results['average_argument_score_100']:.2f}"
)

print(
    f"SC: "
    f"{results['global_coherence']['global_coherence_score_100']:.2f}"
)

print(
    f"DEBATE SCORE: "
    f"{results['debate_score_100']:.2f}"
)


# =====================================
# ARCHIVO
# =====================================

print("\n")
print("=" * 80)
print("ARCHIVO GUARDADO")
print("=" * 80)

print(path)

print("\nProceso finalizado.")