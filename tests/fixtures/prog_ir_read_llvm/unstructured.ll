; irreducible CFG: the h/m cycle has two entries (entry br_conds into
; both h and m) — must yield {ok: False, blockers: ["unstructured_cfg"]}
define i32 @irred(i32 %x) {
entry:
  %c = icmp slt i32 %x, 0
  br i1 %c, label %h, label %m
h:
  %d = icmp slt i32 %x, 100
  br i1 %d, label %m, label %exit
m:
  br label %h
exit:
  ret i32 1
}
