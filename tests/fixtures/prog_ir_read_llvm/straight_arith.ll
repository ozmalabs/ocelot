; single block, integer arithmetic — parse_llvm_ir subset
define i32 @straight(i32 %x, i32 %y) {
  %a = add i32 %x, %y
  %b = mul i32 %a, 3
  %c = sub i32 %b, %y
  %d = add i32 %c, -5
  ret i32 %d
}
