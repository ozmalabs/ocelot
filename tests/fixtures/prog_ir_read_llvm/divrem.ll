; sdiv/srem — truncate-toward-zero; nonzero divisors only (divide-by-
; zero is the documented divergence: oracle raises, IDiv/IRem return 0)
define i32 @divrem(i32 %x, i32 %y) {
  %q = sdiv i32 %x, %y
  %r = srem i32 %x, %y
  %s = mul i32 %q, 10
  %t = add i32 %s, %r
  ret i32 %t
}
