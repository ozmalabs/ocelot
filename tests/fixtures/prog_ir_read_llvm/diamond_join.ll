; CFG diamond with a join block; arm-defined values are dead (the only
; coherent join form in the no-phi dialect) — join reads entry values
define i32 @dj(i32 %x) {
entry:
  %base = mul i32 %x, 3
  %c = icmp sgt i32 %base, 10
  br i1 %c, label %a, label %b
a:
  %da = add i32 %base, 1
  br label %join
b:
  %db = add i32 %base, 2
  br label %join
join:
  %r = add i32 %base, 7
  ret i32 %r
}
