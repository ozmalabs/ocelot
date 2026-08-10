; dominance-violating: join reads a value defined in only one arm.
; The oracle back-computes %da regardless of path; the lifted program
; would trap name:da on the b path → honest blocker, not divergence.
define i32 @jrb(i32 %x) {
entry:
  %c = icmp sgt i32 %x, 0
  br i1 %c, label %a, label %b
a:
  %da = add i32 %x, 5
  br label %join
b:
  br label %join
join:
  ret i32 %da
}
