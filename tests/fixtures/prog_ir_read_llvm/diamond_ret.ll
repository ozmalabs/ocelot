; CFG if-then-else diamond, both arms return (the corpus form —
; without phi, values cannot flow back across a merge)
define i32 @dr(i32 %x) {
entry:
  %doubled = mul i32 %x, 2
  %c = icmp slt i32 %doubled, 100
  br i1 %c, label %small, label %big
small:
  %s = add i32 %doubled, 1
  ret i32 %s
big:
  %b = add i32 %doubled, 100
  ret i32 %b
}
