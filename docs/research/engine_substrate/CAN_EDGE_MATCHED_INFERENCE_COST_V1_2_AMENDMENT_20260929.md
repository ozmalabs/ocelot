# Edge-matched inference cost v1.2 profile amendment (2026-09-29)

The v1.1 result found that a lower maximum bag width did not imply lower measured junction-tree time. Source tracing confirms `junction_tree_map` and `graph_treewidth` are pure Python; the native substrate provides graph storage/extraction, not the message-passing loop. V1.2 therefore captures complete bag-size, separator-size, and elimination-tree child-count histograms for both orders, plus source-aligned loop-work proxies. It retains per-call `tracemalloc` peaks and whole-worker process high-water RSS as distinct measures. No native allocator attribution is claimed for the pure-Python JT routine.

Graph fixtures, factors, orders, oracle, timing procedure, and correctness gates remain unchanged. A fresh lock and complete 36-worker replay bind the expanded profile capture.

