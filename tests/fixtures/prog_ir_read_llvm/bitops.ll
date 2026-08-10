; single block, bitwise ops (non-negative inputs: lshr-of-negative at
; shift 0 is a documented wrap divergence, fixture-avoided)
define i32 @bitops(i32 %x, i32 %y) {
  %a = and i32 %x, %y
  %o = or i32 %a, 12
  %e = xor i32 %o, %y
  %s = shl i32 %e, 2
  %l = lshr i32 %s, 1
  %r = ashr i32 %l, 1
  ret i32 %r
}
