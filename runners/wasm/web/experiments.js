// Curated Interactive Substrate Experiments for OCELOT
// Implements 4 runnable experiments demonstrating the (G, Γ, C) cognitive architecture.

export const EXPERIMENTS = [
  {
    id: "bouba_kiki",
    title: "1. Bouba/Kiki Crossmodal Sound-Symbolism",
    subtitle: "Qualia Space Geometry & Analogical Binding",
    badge: "Cognitive Semantics",
    description: `Demonstrates how phonetic features ("kiki" vs "bouba") and geometric curvature (spiky star vs smooth blob) are independently extracted into graph attributes, projected into a shared <code>phenomenal:sharpness</code> axis in qualia space, and bound via rewrite rules into crossmodal analogical matches without hardcoded scalar comparisons.`,
    citation: "Köhler (1929), Ramachandran & Hubbard (2001), OCELOT domains/bouba_kiki_world.py",

    presets: [
      {
        name: "Sharp Pair: 'kiki' & Spiky Star",
        word: "kiki",
        wordSharpness: 0.92,
        shape: "spiky_star",
        shapeSharpness: 0.88,
        audioFreq: 880,
      },
      {
        name: "Round Pair: 'bouba' & Smooth Blob",
        word: "bouba",
        wordSharpness: 0.12,
        shape: "smooth_blob",
        shapeSharpness: 0.15,
        audioFreq: 180,
      },
      {
        name: "Cross Pair: 'tiki' & Smooth Blob (Mismatch Probe)",
        word: "tiki",
        wordSharpness: 0.82,
        shape: "smooth_blob",
        shapeSharpness: 0.15,
        audioFreq: 750,
      },
      {
        name: "Cross Pair: 'maluma' & Spiky Star (Mismatch Probe)",
        word: "maluma",
        wordSharpness: 0.18,
        shape: "spiky_star",
        shapeSharpness: 0.88,
        audioFreq: 220,
      }
    ],

    async setup(substrate, config, log) {
      log("Seeding Bouba/Kiki grammar productions and ontology...", "info");

      // 1. Register Grammar Productions (Γ)
      const manifest = {
        id: "bouba_kiki_grammar",
        productions: [
          { src: { type: "QualiaDimension", var: "qd" }, edge_type: "has_word", tgt: { type: "Word", var: "w" } },
          { src: { type: "QualiaDimension", var: "qd" }, edge_type: "has_shape", tgt: { type: "Shape", var: "s" } },
          { src: { type: "Word", var: "w" }, edge_type: "projects_to", tgt: { type: "PoleAttribution", var: "p" } },
          { src: { type: "Shape", var: "s" }, edge_type: "projects_to", tgt: { type: "PoleAttribution", var: "p" } },
          { src: { type: "Word", var: "w" }, edge_type: "matches_shape", tgt: { type: "Shape", var: "s" } },
          { src: { type: "AnalogicalMatch", var: "m" }, edge_type: "binds_word", tgt: { type: "Word", var: "w" } },
          { src: { type: "AnalogicalMatch", var: "m" }, edge_type: "binds_shape", tgt: { type: "Shape", var: "s" } }
        ]
      };
      substrate.load_seed_manifest(JSON.stringify(manifest), null);

      // 2. Add Nodes (G)
      const axis = substrate.add_node("QualiaDimension", JSON.stringify({
        name: "phenomenal:sharpness",
        family: "phenomenal",
        pole_pos: "sharp",
        pole_neg: "round"
      }));

      const wordNode = substrate.add_node("Word", JSON.stringify({
        name: config.word,
        phonetic_sharpness: config.wordSharpness
      }));

      const shapeNode = substrate.add_node("Shape", JSON.stringify({
        name: config.shape,
        curvature_sharpness: config.shapeSharpness
      }));

      // 3. Connect initial edges
      substrate.add_edge(axis, "has_word", wordNode, null);
      substrate.add_edge(axis, "has_shape", shapeNode, null);

      // 4. Install Rewrite Rules (C)
      const rWordSharp = {
        name: "project_word_sharp",
        match: [["axis", "has_word", "w"]],
        where: {
          type: "And",
          items: [
            { type: "Gte", a: { type: "Attr", node: { type: "Var", name: "w" }, key: "phonetic_sharpness" }, b: { type: "Lit", value: 0.5 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "w" }, edge_type: "projects_to" }, var_name: "p", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "p", "PoleAttribution", { "pole": "sharp", "dimension": "sharpness" }],
          ["add_edge", "w", "projects_to", "p", {}]
        ]
      };

      const rWordRound = {
        name: "project_word_round",
        match: [["axis", "has_word", "w"]],
        where: {
          type: "And",
          items: [
            { type: "Lt", a: { type: "Attr", node: { type: "Var", name: "w" }, key: "phonetic_sharpness" }, b: { type: "Lit", value: 0.5 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "w" }, edge_type: "projects_to" }, var_name: "p", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "p", "PoleAttribution", { "pole": "round", "dimension": "sharpness" }],
          ["add_edge", "w", "projects_to", "p", {}]
        ]
      };

      const rShapeSharp = {
        name: "project_shape_sharp",
        match: [["axis", "has_shape", "s"]],
        where: {
          type: "And",
          items: [
            { type: "Gte", a: { type: "Attr", node: { type: "Var", name: "s" }, key: "curvature_sharpness" }, b: { type: "Lit", value: 0.5 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "s" }, edge_type: "projects_to" }, var_name: "p", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "p", "PoleAttribution", { "pole": "sharp", "dimension": "sharpness" }],
          ["add_edge", "s", "projects_to", "p", {}]
        ]
      };

      const rShapeRound = {
        name: "project_shape_round",
        match: [["axis", "has_shape", "s"]],
        where: {
          type: "And",
          items: [
            { type: "Lt", a: { type: "Attr", node: { type: "Var", name: "s" }, key: "curvature_sharpness" }, b: { type: "Lit", value: 0.5 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "s" }, edge_type: "projects_to" }, var_name: "p", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "p", "PoleAttribution", { "pole": "round", "dimension": "sharpness" }],
          ["add_edge", "s", "projects_to", "p", {}]
        ]
      };

      const rBind = {
        name: "bind_crossmodal_analogy",
        match: [
          ["w", "projects_to", "pw"],
          ["s", "projects_to", "ps"]
        ],
        where: {
          type: "And",
          items: [
            { type: "Eq", a: { type: "Attr", node: { type: "Var", name: "pw" }, key: "pole" }, b: { type: "Attr", node: { type: "Var", name: "ps" }, key: "pole" } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "w" }, edge_type: "matches_shape" }, var_name: "m", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "m", "AnalogicalMatch", { "qualia": "sharpness", "grounding": "crossmodal" }],
          ["add_edge", "w", "matches_shape", "s", {}],
          ["add_edge", "m", "binds_word", "w", {}],
          ["add_edge", "m", "binds_shape", "s", {}]
        ]
      };

      substrate.add_rule(JSON.stringify(rWordSharp));
      substrate.add_rule(JSON.stringify(rWordRound));
      substrate.add_rule(JSON.stringify(rShapeSharp));
      substrate.add_rule(JSON.stringify(rShapeRound));
      substrate.add_rule(JSON.stringify(rBind));

      log(`Seeded Word('${config.word}') and Shape('${config.shape}'). 5 rules ready.`, "success");
      return { wordNode, shapeNode, axis };
    }
  },

  {
    id: "counterfactual",
    title: "2. Counterfactual Rehearsal & Epistemic Scope",
    subtitle: "Hypothesis Testing Without Belief Contamination",
    badge: "Cognitive Control",
    description: `Demonstrates the substrate's default mode network spawning an ungrounded <code>ImagineRequest</code> to rehearse a hypothesis experiment. Rehearsal results are isolated as counterfactual evidence and forbidden by the grammar from being promoted directly to grounded truth.`,
    citation: "OCELOT seeds/counterfactual_experiment.json",

    presets: [
      {
        name: "Ablation Hypothesis: 'Disable Inhibitory Gate'",
        hypothesis: "Inhibitory ablation induces hyper-activation cascade",
        scope: "graph_counterfactual",
      },
      {
        name: "Gain Modulation: 'Boost Saccadic Salience'",
        hypothesis: "Elevated foveation gain accelerates visual convergence",
        scope: "graph_counterfactual",
      }
    ],

    async setup(substrate, config, log) {
      log("Seeding counterfactual experiment grammar and productions...", "info");

      // 1. Register Grammar Productions (Γ)
      const manifest = {
        id: "counterfactual_grammar",
        productions: [
          { src: { type: "Agent", var: "a" }, edge_type: "proposes_experiment", tgt: { type: "Experiment", var: "e" } },
          { src: { type: "ImagineRequest", var: "req" }, edge_type: "rehearses_experiment", tgt: { type: "Experiment", var: "e" } },
          { src: { type: "ImagineRequest", var: "req" }, edge_type: "produced_imagination", tgt: { type: "Imagination", var: "img" } },
          { src: { type: "Experiment", var: "e" }, edge_type: "has_counterfactual_evidence", tgt: { type: "Imagination", var: "img" } }
        ]
      };
      substrate.load_seed_manifest(JSON.stringify(manifest), null);

      // 2. Add Base Agent and Experiment Nodes (G)
      const agentNode = substrate.add_node("Agent", JSON.stringify({ name: "ocelot_core" }));
      const expNode = substrate.add_node("Experiment", JSON.stringify({
        status: "counterfactual_requested",
        epistemic_scope: config.scope,
        hypothesis: config.hypothesis
      }));
      substrate.add_edge(agentNode, "proposes_experiment", expNode, null);

      // 3. Install Rules (C)
      const rRehearse = {
        name: "ce_rehearse_graph_native_hypothesis",
        match: [["a", "proposes_experiment", "e"]],
        where: {
          type: "And",
          items: [
            { type: "Eq", a: { type: "Attr", node: { type: "Var", name: "e" }, key: "status" }, b: { type: "Lit", value: "counterfactual_requested" } },
            { type: "Not", arg: { type: "Exists", source: { type: "InNeighbours", node: { type: "Var", name: "e" }, edge_type: "rehearses_experiment" }, var_name: "req", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "req", "ImagineRequest", { "status": "requested", "kind": "self_experiment", "why": "test_hypothesis" }],
          ["add_edge", "req", "rehearses_experiment", "e", {}],
          ["set_attr", "e", "status", "counterfactual_running"]
        ]
      };

      const rSimulate = {
        name: "ce_simulate_imagined_outcome",
        match: [["req", "rehearses_experiment", "e"]],
        where: {
          type: "And",
          items: [
            { type: "Eq", a: { type: "Attr", node: { type: "Var", name: "e" }, key: "status" }, b: { type: "Lit", value: "counterfactual_running" } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "req" }, edge_type: "produced_imagination" }, var_name: "img", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "img", "Imagination", { "rehearsal_result": "predicted_cascade_confirmed", "confidence": 0.88 }],
          ["add_edge", "req", "produced_imagination", "img", {}],
          ["set_attr", "e", "status", "simulation_produced"]
        ]
      };

      const rRetain = {
        name: "ce_retain_imagination_as_non_oracular_evidence",
        match: [
          ["req", "rehearses_experiment", "e"],
          ["req", "produced_imagination", "img"]
        ],
        where: {
          type: "Eq",
          a: { type: "Attr", node: { type: "Var", name: "e" }, key: "status" },
          b: { type: "Lit", value: "simulation_produced" }
        },
        effects: [
          ["add_edge", "e", "has_counterfactual_evidence", "img", {}],
          ["set_attr", "e", "status", "counterfactual_done"],
          ["set_attr", "e", "evidence_kind", "imagined_non_oracular"],
          ["set_attr", "e", "requires_external_validation", 1]
        ]
      };

      substrate.add_rule(JSON.stringify(rRehearse));
      substrate.add_rule(JSON.stringify(rSimulate));
      substrate.add_rule(JSON.stringify(rRetain));

      log(`Created Experiment(#${expNode}) linked to Agent(#${agentNode}). Rehearsal rules installed.`, "success");
      return { expNode, agentNode };
    }
  },

  {
    id: "qualia_reconstruction",
    title: "3. Qualia Reconstruction & Observer Aperture",
    subtitle: "Visual Scene Memory Retrieval Across Aperture Filters",
    badge: "Visual Perception",
    description: `Tests how an object cue (e.g. <code>Apple</code>) retrieves arbitrary episodic visual details (hue, contour, bite, specular lighting) under 4 observer aperture settings: Direct Perception, Full Visualization, Coarse Visualization, and Absent/Semantic Control.`,
    citation: "OCELOT docs/experiments/qualia-visualization-development-plan.md, domains/qualia_visualization_world.py",

    presets: [
      {
        name: "Aperture 1: Direct Perception (Full Feature Access)",
        aperture: "direct_perception",
        apertureLevel: 3,
        cue: "apple",
      },
      {
        name: "Aperture 2: Full Visualization (Complete Mental Imagery)",
        aperture: "full_visualization",
        apertureLevel: 2,
        cue: "apple",
      },
      {
        name: "Aperture 3: Coarse Visualization (Geometry Only)",
        aperture: "coarse_visualization",
        apertureLevel: 1,
        cue: "apple",
      },
      {
        name: "Aperture 4: Semantic Control (Category Accessible, Zero Visuals)",
        aperture: "semantic_control",
        apertureLevel: 0,
        cue: "apple",
      }
    ],

    async setup(substrate, config, log) {
      log(`Setting up qualia reconstruction with aperture '${config.aperture}'...`, "info");

      // 1. Register Grammar Productions (Γ)
      const manifest = {
        id: "qualia_reconstruction_grammar",
        productions: [
          { src: { type: "Concept", var: "c" }, edge_type: "recalls_memory", tgt: { type: "VisualMemory", var: "m" } },
          { src: { type: "Concept", var: "c" }, edge_type: "projects_scene", tgt: { type: "ImaginedScene", var: "s" } },
          { src: { type: "Concept", var: "c" }, edge_type: "semantic_verdict", tgt: { type: "SemanticReport", var: "r" } },
          { src: { type: "ImaginedScene", var: "s" }, edge_type: "has_feature", tgt: { type: "FeatureState", var: "f" } }
        ]
      };
      substrate.load_seed_manifest(JSON.stringify(manifest), null);

      // 2. Add Nodes (G)
      const cueNode = substrate.add_node("Concept", JSON.stringify({
        name: config.cue,
        category: "fruit",
        aperture_level: config.apertureLevel
      }));

      const memNode = substrate.add_node("VisualMemory", JSON.stringify({
        source_concept: config.cue,
        hue: "crimson",
        contour: "lobed_sphere",
        stem_angle: 15,
        bite_location: "upper_right",
        lighting: "specular"
      }));
      substrate.add_edge(cueNode, "recalls_memory", memNode, null);

      // 3. Rules for Aperture Filtering (C)
      const rFull = {
        name: "reconstruct_full_imagery",
        match: [["c", "recalls_memory", "m"]],
        where: {
          type: "And",
          items: [
            { type: "Gte", a: { type: "Attr", node: { type: "Var", name: "c" }, key: "aperture_level" }, b: { type: "Lit", value: 2 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "c" }, edge_type: "projects_scene" }, var_name: "s", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "s", "ImaginedScene", { "resolution": "high", "rendered": true }],
          ["add_node", "f1", "FeatureState", { "kind": "hue", "val": "crimson" }],
          ["add_node", "f2", "FeatureState", { "kind": "contour", "val": "lobed_sphere" }],
          ["add_node", "f3", "FeatureState", { "kind": "stem", "val": "vertical_offset" }],
          ["add_node", "f4", "FeatureState", { "kind": "bite", "val": "present" }],
          ["add_edge", "s", "has_feature", "f1", {}],
          ["add_edge", "s", "has_feature", "f2", {}],
          ["add_edge", "s", "has_feature", "f3", {}],
          ["add_edge", "s", "has_feature", "f4", {}],
          ["add_edge", "c", "projects_scene", "s", {}]
        ]
      };

      const rCoarse = {
        name: "reconstruct_coarse_imagery",
        match: [["c", "recalls_memory", "m"]],
        where: {
          type: "And",
          items: [
            { type: "Eq", a: { type: "Attr", node: { type: "Var", name: "c" }, key: "aperture_level" }, b: { type: "Lit", value: 1 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "c" }, edge_type: "projects_scene" }, var_name: "s", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "s", "ImaginedScene", { "resolution": "coarse_bounding", "rendered": true }],
          ["add_node", "f1", "FeatureState", { "kind": "contour", "val": "lobed_sphere" }],
          ["add_edge", "s", "has_feature", "f1", {}],
          ["add_edge", "c", "projects_scene", "s", {}]
        ]
      };

      const rSemantic = {
        name: "report_semantic_category_only",
        match: [["c", "recalls_memory", "m"]],
        where: {
          type: "And",
          items: [
            { type: "Eq", a: { type: "Attr", node: { type: "Var", name: "c" }, key: "aperture_level" }, b: { type: "Lit", value: 0 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "c" }, edge_type: "semantic_verdict" }, var_name: "r", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "r", "SemanticReport", { "category": "fruit", "visual_coordinates": "absent" }],
          ["add_edge", "c", "semantic_verdict", "r", {}]
        ]
      };

      substrate.add_rule(JSON.stringify(rFull));
      substrate.add_rule(JSON.stringify(rCoarse));
      substrate.add_rule(JSON.stringify(rSemantic));

      log(`Concept cue '${config.cue}' linked to VisualMemory. Ready to reconstruct.`, "success");
      return { cueNode, memNode };
    }
  },

  {
    id: "border_ownership",
    title: "4. Figure-Ground Border Ownership Attribution",
    subtitle: "V2/V4 Neurophysiology of Boundary Assignment",
    badge: "Visual Neuroscience",
    description: `Reproduces the neurophysiology of border ownership (Zhou et al. 2000): resolving which of two overlapping visual surfaces owns the separating contour edge using local contrast tokens and global convexity rewrite rules.`,
    citation: "Zhou et al. (2000), OCELOT domains/border_ownership_world.py, seeds/vision_border_ownership.json",

    presets: [
      {
        name: "Foreground Occlusion: Square over Background",
        foreground: "OccludingSquare",
        background: "BackdropSurface",
        junctionType: "T_junction",
        convexSide: "foreground",
      },
      {
        name: "Convex Enclosure: Circular Disk in Basin",
        foreground: "CircularDisk",
        background: "SurroundingField",
        junctionType: "closed_contour",
        convexSide: "foreground",
      }
    ],

    async setup(substrate, config, log) {
      log("Seeding visual surfaces and boundary edge tokens...", "info");

      // 1. Register Grammar Productions (Γ)
      const manifest = {
        id: "border_ownership_grammar",
        productions: [
          { src: { type: "Surface", var: "s" }, edge_type: "shares_boundary", tgt: { type: "RetinalToken", var: "b" } },
          { src: { type: "RetinalToken", var: "b" }, edge_type: "owned_by", tgt: { type: "Surface", var: "s" } },
          { src: { type: "FigureGroundVerdict", var: "v" }, edge_type: "identified_figure", tgt: { type: "Surface", var: "s" } },
          { src: { type: "FigureGroundVerdict", var: "v" }, edge_type: "identified_ground", tgt: { type: "Surface", var: "s" } }
        ]
      };
      substrate.load_seed_manifest(JSON.stringify(manifest), null);

      // 2. Surfaces (G)
      const fg = substrate.add_node("Surface", JSON.stringify({
        label: config.foreground,
        role: "candidate_figure",
        convexity: 1.0
      }));

      const bg = substrate.add_node("Surface", JSON.stringify({
        label: config.background,
        role: "candidate_ground",
        convexity: 0.0
      }));

      const bToken = substrate.add_node("RetinalToken", JSON.stringify({
        kind: "boundary_contour",
        contrast_gradient: "left_to_right",
        junction: config.junctionType
      }));

      substrate.add_edge(fg, "shares_boundary", bToken, null);
      substrate.add_edge(bg, "shares_boundary", bToken, null);

      // 3. Border ownership rewrite rule (C)
      const rBorder = {
        name: "assign_border_ownership_to_convex_figure",
        match: [
          ["fg", "shares_boundary", "b"],
          ["bg", "shares_boundary", "b"]
        ],
        where: {
          type: "And",
          items: [
            { type: "Gt", a: { type: "Attr", node: { type: "Var", name: "fg" }, key: "convexity" }, b: { type: "Lit", value: 0.5 } },
            { type: "Lt", a: { type: "Attr", node: { type: "Var", name: "bg" }, key: "convexity" }, b: { type: "Lit", value: 0.5 } },
            { type: "Not", arg: { type: "Exists", source: { type: "Neighbours", node: { type: "Var", name: "b" }, edge_type: "owned_by" }, var_name: "s", predicate: { type: "Lit", value: true } } }
          ]
        },
        effects: [
          ["add_node", "v", "FigureGroundVerdict", { "status": "resolved", "border_ownership_side": "figure" }],
          ["add_edge", "b", "owned_by", "fg", {}],
          ["add_edge", "v", "identified_figure", "fg", {}],
          ["add_edge", "v", "identified_ground", "bg", {}]
        ]
      };

      substrate.add_rule(JSON.stringify(rBorder));
      log(`Surfaces and RetinalToken seeded with boundary rule.`, "success");
      return { fg, bg, bToken };
    }
  }
];
