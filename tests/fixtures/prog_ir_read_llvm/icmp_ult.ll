; unsigned predicate: parse accepts it, but llvm_ir_interp (the trusted
; oracle) refuses — the lift refuses too (unsupported_opcode:icmp_ult)
define i1 @ult(i32 %x, i32 %y) {
  %c = icmp ult i32 %x, %y
  ret i1 %c
}
