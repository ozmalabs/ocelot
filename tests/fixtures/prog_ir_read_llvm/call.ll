; OUT OF PARSE SCOPE: neither parse_llvm_ir nor parse_llvm_cfg speaks
; `call` — parsing this file must raise (honest parse-layer residual).
; The call → ProgCallExtern correspondence row is gated graph-level.
define i32 @callabs(i32 %x) {
  %r = call i32 @abs(i32 %x)
  ret i32 %r
}
