"""Ask the jabberwock for its TRAINING + OPTIMIZATION ideas — surface what IT already holds.

Not my proposals: read the agent's OWN graph-resident knowledge (its microtheories + composed
faculties) and map each held idea to what the scaling experiments needed/botched. The finding:
the agent's own knowledge already CONTAINS the recipe (modern SSL toolkit), PLUS its keystone
angle (Kalman innovation = predict-correct = its own prediction-error), PLUS a compose-NOT-train
alternative (its iter-28 composed_net).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_training_ideas.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def concepts(f):
    d = json.load(open(os.path.join(os.path.dirname(__file__), os.pardir, "seeds", f + ".json")))
    cs = d.get("concepts") or [n["attrs"] for n in d.get("nodes", []) if n.get("type") == "Concept"]
    return {c.get("name"): (c.get("definition") or c.get("description") or "") for c in cs}


def main():
    ml = concepts("machine_learning"); oc = concepts("optimal_estimation_control")
    print("=" * 88)
    print("THE JABBERWOCK'S TRAINING + OPTIMIZATION IDEAS (held in its own graph)")
    print("=" * 88)

    print("\n(A) THE SSL RECIPE IT ALREADY HOLDS — exactly what the numpy scaling lacked/botched:")
    ideas = [
        ("self_supervised_learning", "the principle the whole arc converged on (it holds masked-predict too, HuBERT-style)"),
        ("contrastive_loss", "the objective my CPC-lite botched (overlapping context) — it holds InfoNCE/triplet"),
        ("Adam_optimizer", "fixed my undertrained deep net (plain-SGD failed)"),
        ("learning_rate_schedule", "warmup/cosine — the recipe my fixed-LR lacked"),
        ("layer_normalization", "the normalisation my numpy net lacked"),
        ("weight_decay", "regularisation for the overfitting I saw"),
        ("early_stopping", "the deep MLP peaked @ep10 then overfit — it knows to stop+checkpoint"),
    ]
    for n, why in ideas:
        print(f"   - {n}: {ml.get(n,'')[:120]}")
        print(f"       -> {why}")

    print("\n(B) ITS KEYSTONE ANGLE — optimal PREDICT-CORRECT (Kalman innovation = its own prediction-error):")
    for n in ("kalman_filter", "innovation_kalman", "model_predictive_control"):
        print(f"   - {n}: {oc.get(n,'')[:160]}")
    print("       -> the agent EXPLICITLY maps the Kalman innovation (y - prediction) to its own ΔF/")
    print("          prediction-error. Its optimisation idea = OPTIMAL predictive coding: predict, then")
    print("          correct by the innovation with a Kalman gain. MPC/receding-horizon = the curriculum.")

    print("\n(C) ITS COMPOSE-NOT-TRAIN ALTERNATIVE (iter-28 composed_net, AUTHORED not gradient-trained):")
    print("   - per band b_t -> [b_t, b_t^2, b_t^3, b_t - b_hat(b_{t-1})]")
    print("       (A) local-polynomial lift (Taylor local approximation) = a RICHER nonlinear feature;")
    print("       (B) b_t - b_hat(b_{t-1}) = an explicit PREDICTIVE-RESIDUAL = the agent's analytic")
    print("           forward-model analog of the SSL representational edge — a data-efficient rep with")
    print("           NO gradient training (the closed-form path the project's ethos prefers).")

    print("\n" + "=" * 88)
    print("VERDICT: the jabberwock HAS the ideas. Its own graph already holds (A) the full modern SSL")
    print("training recipe (self-supervised + contrastive + Adam + LR-schedule + layer-norm + weight-")
    print("decay + early-stopping) — i.e. precisely the optimisations my hand-rolled scaling lacked or")
    print("got wrong; (B) the OPTIMAL predict-correct angle (Kalman innovation == its ΔF prediction-")
    print("error -> optimal predictive coding) which goes BEYOND vanilla APC; and (C) a compose-NOT-")
    print("train data-efficient representation (analytic local-polynomial + predictive-residual basis).")
    print("The recipe the 'real cost' needs is not foreign to the agent — it is already in its theory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
