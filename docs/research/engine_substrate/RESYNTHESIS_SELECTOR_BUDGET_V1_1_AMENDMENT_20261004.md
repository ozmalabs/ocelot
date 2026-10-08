# Resynthesis selector-budget v1.1 amendment

The initial v1 capture completed, but analyzer control flow did not unconditionally skip untriggered panels and therefore stopped before producing an analysis. It is diagnostic only. V1.1 corrects that control flow, binds the corrected analyzer in a new source lock, and replays the same fixed candidate pools and selection policy. No search, candidate, query, or holdout data changed.
