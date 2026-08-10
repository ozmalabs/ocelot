; natural single-latch loop. NO PHI in this dialect → no loop-carried
; value: the loop runs 0 iterations (x >= 10) or forever (x < 10).
; Zero-iteration inputs gate exact agreement; looping inputs gate
; agreement-of-refusal (interp max_steps vs ProgEval fuel).
define i32 @loopz(i32 %x) {
entry:
  %lim = add i32 %x, 0
  br label %head
head:
  %c = icmp slt i32 %lim, 10
  br i1 %c, label %body, label %exit
body:
  %junk = add i32 %lim, 1
  br label %head
exit:
  ret i32 %lim
}
